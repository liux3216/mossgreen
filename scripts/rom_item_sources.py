"""Read map-attached item rewards and shops in the Mossgreen ROM."""
from collections import Counter

from rom_field_scripts import FieldScripts

ITEM_COUNT = 375
GIFT = 'NPC赠送／事件奖励'
PICKUP = '地面拾取'
HIDDEN = '隐藏道具'
SHOP = '商店购买'


def scan_script(rom, start, origin, record, unknown, limit=2000):
    # Visit each path with its known item variables and pending script returns.
    todo = [(start, (), ())]
    seen = set()
    while todo and len(seen) < limit:
        pc, returns, known = todo.pop()
        variables = dict(known)

        def resolve(value):
            return value if value < 0x4000 else variables.get(value)

        while rom.valid(pc) and len(seen) < limit:
            state = (pc, returns, tuple(sorted(variables.items())))
            if state in seen:
                break
            seen.add(state)

            op = rom.byte(pc)
            if op == 0x5C:
                mode = rom.byte(pc + 1)
                size = {0: 14, 1: 18, 2: 18, 3: 10, 4: 18,
                        5: 14, 6: 22, 7: 18, 8: 22, 9: 14}.get(mode)
                if mode in (1, 2, 6, 8):
                    target = rom.word(pc + size - 4)
                    todo.append((target, returns, state[2]))
            else:
                size = rom.widths.get(op)
            if not size:
                unknown[op] += 1
                break

            next_pc = pc + size
            if op in (0x16, 0x17, 0x18, 0x19, 0x1A):
                var, value = rom.unpack('<HH', pc + 1)
                if op == 0x19:
                    value = variables.get(value)
                elif op == 0x1A:
                    value = resolve(value)
                elif op in (0x17, 0x18):
                    current = variables.get(var)
                    value = None if current is None else (current + (value if op == 0x17 else -value)) & 0xFFFF
                if value is None:
                    variables.pop(var, None)
                else:
                    variables[var] = value
            elif op in (0x08, 0x09, 0x0A, 0x0B):
                standard_script = rom.byte(pc + (1 if op in (0x08, 0x09) else 2))
                if standard_script in (0, 1):
                    record(variables.get(0x8000), PICKUP if standard_script == 1 else GIFT, origin, pc)
                if op == 0x08:
                    break
            elif op == 0x44:
                record(resolve(rom.half(pc + 1)), GIFT, origin, pc)
            elif op == 0x86:
                shop = rom.word(pc + 1)
                if rom.valid(shop):
                    for index in range(128):
                        item = rom.half(shop + 2 * index)
                        if not 0 < item < ITEM_COUNT:
                            break
                        record(item, SHOP, origin, pc)

            if op in (2, 0x0D, 0x24):
                break
            if op == 3:
                if not returns:
                    break
                pc, returns = returns[-1], returns[:-1]
                continue
            if op in (4, 5):
                if len(returns) >= 8:
                    break
                if op == 4:
                    returns += (next_pc,)
                pc = rom.word(pc + 1)
                continue
            if op in (6, 7) and len(returns) < 8:
                branch_returns = returns + ((next_pc,) if op == 7 else ())
                todo.append((rom.word(pc + 2), branch_returns, state[2]))
            pc = next_pc
    return len(seen) >= limit


def collect_item_sources(payload, root, places, item_ids):
    field = FieldScripts(payload, root)
    sources = {item_id: {} for item_id in item_ids}
    audit = []
    unknown = Counter()
    roots = limited = 0

    def record(item_id, method, origin, instruction):
        if item_id not in sources:
            return
        place = places[origin['mapId']]
        map_id = place['mapId']
        sources[item_id][map_id, method] = {
            'mapId': map_id, 'name': place['name'], 'path': place['path'], 'method': method,
        }
        audit.append({'item': item_id, 'mapId': map_id, 'method': method,
                      'origin': origin, 'instruction': hex(instruction)})

    for address, origins in field.roots.items():
        for origin in origins:
            if origin['mapId'] in places:
                roots += 1
                limited += scan_script(field, address, origin, record, unknown)

    for map_id in sorted(places.keys() & field.maps.keys()):
        events = field.word(field.maps[map_id]['header'] + 4)
        backgrounds = field.word(events + 16)
        for index in range(field.byte(events + 3)):
            address = backgrounds + 12 * index
            if field.byte(address + 5) == 7:
                record(field.half(address + 8), HIDDEN,
                       {'mapId': map_id, 'kind': 'hidden'}, address)

    return sources, {'roots': roots, 'limitedRoots': limited,
                     'unknownOpcodes': dict(unknown), 'sources': audit}
