"""Build the item catalog from the Chinese Mossgreen ROM and the wiki's map data."""
import argparse
import base64
from collections import defaultdict
from io import BytesIO
import json
from pathlib import Path

from PIL import Image

from rom_field_scripts import FieldScripts
from rom_item_sources import ITEM_COUNT, collect_item_sources
import rom_map_renderer

ROOT = Path(__file__).resolve().parent.parent
POCKETS = {1: '道具', 2: '重要道具', 3: '精灵球', 4: '招式学习机', 5: '树果'}
ICON_TABLE = 0x083D4294
SPECIES_INFO = 0x08B5C1E0
WILD_ITEM = '野生宝可梦携带'
# These three descriptions are in Portuguese in the Chinese ROM.
LOCALIZED = {
    275: ('无限船票', '前往相应地区乘船所需的船票。'),
    281: ('1号舱房钥匙', '打开废弃船上 1 号房间的钥匙，年代久远，似乎很容易折断。'),
    374: ('蓝宝石', '散发蓝色光辉的稀有宝石。'),
}


def data(name):
    return json.loads((ROOT / 'data' / (name + '.json')).read_text())


def icon(field, item_id):
    picture, palette = field.unpack('<II', ICON_TABLE + item_id * 8)
    pixels = rom_map_renderer.lz(picture)
    colors = rom_map_renderer.lz(palette)
    assert len(pixels) == 288 and len(colors) == 32
    image = Image.new('P', (24, 24))
    image.putpalette([
        (int.from_bytes(colors[i:i + 2], 'little') >> shift & 31) * 255 // 31
        for i in range(0, 32, 2) for shift in (0, 5, 10)
    ] + [0] * (768 - 48))
    for tile in range(9):
        tile_x, tile_y = tile % 3 * 8, tile // 3 * 8
        for iy in range(8):
            for ix in range(8):
                value = pixels[tile * 32 + iy * 4 + ix // 2]
                image.putpixel((tile_x + ix, tile_y + iy), (value >> (4 * (ix % 2))) & 15)
    buffer = BytesIO()
    image.save(buffer, format='PNG', bits=4, transparency=0)
    return base64.b64encode(buffer.getvalue()).decode('ascii')


def item_rows(field, machines):
    items = field.word(0x1C8)
    assert items == 0x083DB028
    for item_id in range(1, ITEM_COUNT):
        address = items + item_id * 44
        stored_id, price = field.unpack('<HH', address + 14)
        if not stored_id:
            continue
        # This ROM stores 255 in the row for the slot addressed as item 36.
        assert stored_id == item_id or (item_id, stored_id) == (36, 255)
        raw_name = field.text(address, 14)
        pocket = POCKETS[field.byte(address + 26)]
        description = field.text(field.word(address + 20), 180)
        name, description = LOCALIZED.get(item_id, (raw_name, description))
        row = {
            'id': item_id, 'name': name, 'pocket': pocket,
            'price': price or None, 'icon': icon(field, item_id),
            'description': normalize_description(description),
        }
        if raw_name != name:
            row['alias'] = raw_name
        if item_id in machines:
            machine = machines[item_id]
            row['name'] = f"{machine['id']}「{machine['name']}」"
            row['machine'] = machine['id']
        yield row


def normalize_description(text):
    lines = text.splitlines()
    joined = ''
    for line in lines:
        line = line.strip()
        if joined and line and joined[-1:].isascii() and line[:1].isascii():
            joined += ' '
        joined += line
    return joined.replace('�Y', '～').replace(',', '，').replace('.', '。').strip()


def wild_sources(field, places, variants, items):
    pokemon = data('pokemon')
    holders = defaultdict(dict)
    for name, map_id, _, _, encounters in data('encounters'):
        if map_id not in places:
            continue
        place = variants.get((map_id, name), places[map_id])
        for species, *_ in encounters:
            mon = pokemon.get(str(species))
            if not mon or not all(mon['stats'].values()):
                continue
            common, rare = field.unpack('<HH', SPECIES_INFO + species * 28 + 12)
            for item_id, chance in ((common, 100),) if common == rare else ((common, 50), (rare, 5)):
                if item_id not in items:
                    continue
                key = item_id, place['path']
                holders[key][species] = {
                    'id': mon.get('canonicalId', species), 'name': mon['name'], 'chance': chance,
                }

    by_path = {place['path']: place for place in variants.values()}
    for (item_id, path), matches in holders.items():
        place = by_path[path]
        yield item_id, {
            'mapId': place['mapId'], 'name': place['name'], 'path': place['path'],
            'method': WILD_ITEM,
            'holders': sorted(matches.values(), key=lambda mon: (-mon['chance'], mon['name'], mon['id'])),
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rom', type=Path)
    args = parser.parse_args()
    payload = args.rom.read_bytes()
    field = FieldScripts(payload, ROOT)
    rom_map_renderer.load_rom(payload)
    machines = {machine['itemId']: machine for machine in data('machines')}
    items = {row['id']: row for row in item_rows(field, machines)}
    variants = {
        (place['mapId'], place['name']): place for place in data('atlas')
        if (ROOT / place['path'] / 'index.html').exists()
        and (ROOT / 'locations/data' / (place['key'] + '.json')).exists()
    }
    places = {}
    for place in variants.values():
        places.setdefault(place['mapId'], place)
    by_item, audit = collect_item_sources(payload, ROOT, places, items)
    for row in items.values():
        methods = by_item[row['id']]
        machine = machines.get(row['id'])
        if machine:
            for source in machine['locations']:
                map_id, method = source['mapId'], source['method']
                if map_id in places:
                    place = places[map_id]
                    methods[map_id, method] = {
                        'mapId': map_id, 'name': place['name'], 'path': place['path'], 'method': method,
                    }
        row['locations'] = sorted(methods.values(), key=lambda entry: (entry['method'], entry['name']))
    for item_id, entry in wild_sources(field, places, variants, items):
        items[item_id]['locations'].append(entry)

    assert items[1]['name'] == '大师球' and items[13]['price'] == 300
    assert items[340]['name'] == 'HM02「飞翔」' and 52 not in items
    output = ROOT / 'data/items.json'
    output.write_text(json.dumps(list(items.values()), ensure_ascii=False, separators=(',', ':')) + '\n')
    print(f'{len(items)} items, {sum(bool(row["locations"]) for row in items.values())} with sources, '
          f'{sum(len(row["locations"]) for row in items.values())} location/method records')
    print(f'{audit["roots"]} field script roots, {audit["limitedRoots"]} reached the scan limit')


if __name__ == '__main__':
    main()
