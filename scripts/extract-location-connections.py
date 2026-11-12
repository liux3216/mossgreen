"""Extract boundary connections and usable warp destinations for wiki locations.

Usage: python3 scripts/extract-location-connections.py game.gba
Only existing wiki destinations are included. Shared rooms with the 0x7f return
warp use the maps that actually have an entrance into that room.
"""
import json
import struct
import sys
from collections import Counter
from pathlib import Path

root = Path(__file__).resolve().parent.parent
rom = Path(sys.argv[1]).read_bytes()
places = json.loads((root / 'data/locations.json').read_text())
places += json.loads((root / 'data/atlas-extra-locations.json').read_text())
by_id = {}
for p in places:
    # Encounter configurations share one physical map; use its first detail page.
    by_id.setdefault(p['mapId'], p)
assert not {'1/64', '10/30'} & by_id.keys()


def valid(pointer):
    return 0x08000000 <= pointer < 0x08000000 + len(rom)


def unpack(fmt, address):
    return struct.unpack_from(fmt, rom, address & 0x1ffffff)


def word(address):
    return unpack('<I', address)[0]


maps = {}
for key in by_id:
    group, number = map(int, key.split('/'))
    header = word(word(0x3526a8 + group * 4) + number * 4)
    assert valid(header), key
    layout, events, _, connection = unpack('<IIII', header)
    assert valid(layout) and valid(events), key
    width, height = unpack('<II', layout)
    assert 0 < width <= 256 and 0 < height <= 256, key
    count = unpack('<BBBB', events)[1]
    pointer = word(events + 8)
    assert not count or valid(pointer), key
    warps = [unpack('<hhBBBB', pointer + 8 * i) for i in range(count)]
    boundaries = []
    if valid(connection):
        count, pointer = unpack('<II', connection)
        assert count <= 16 and (not count or valid(pointer)), key
        boundaries = [unpack('<IiBBH', pointer + 12 * i) for i in range(count)]
    maps[key] = {'warps': warps, 'boundaries': boundaries, 'size': (width, height)}

graph = {key: {} for key in by_id}
counts = Counter()


def connect(source, target, label):
    if target not in by_id or target == source:
        return
    p = by_id[target]
    entry = graph[source].setdefault(target, {
        'name': p['name'], 'mapId': target,
        'path': 'locations/' + p['anchor'].removeprefix('location-') + '/',
        'routes': [],
    })
    if label not in entry['routes']:
        entry['routes'].append(label)
        counts[label] += 1


directions = {1: '南侧', 2: '北侧', 3: '西侧', 4: '东侧'}
for source, data in maps.items():
    for direction, offset, group, number, _ in data['boundaries']:
        if direction in directions:
            connect(source, f'{group}/{number}', directions[direction])
    width, height = data['size']
    for x, y, elevation, destination_warp, number, group in data['warps']:
        if not (0 <= x < width and 0 <= y < height):
            counts['ignored_invalid_coordinates'] += 1
            continue
        target = f'{group}/{number}'
        if target not in maps or target == source:
            continue
        target_warps = maps[target]['warps']
        if destination_warp >= len(target_warps):
            counts['ignored_invalid_destination_warp'] += 1
            continue
        tx, ty, _, _, return_number, return_group = target_warps[destination_warp]
        tw, th = maps[target]['size']
        if not (0 <= tx < tw and 0 <= ty < th):
            counts['ignored_invalid_destination_coordinates'] += 1
            continue
        connect(source, target, '出入口')
        # 0x7f is the engine's saved entrance return, not a fixed map ID.
        # 0xff placeholder events must not be treated as return warps.
        if (return_group, return_number) == (127, 127):
            connect(target, source, '返回入口')

output = {}
for source, targets in graph.items():
    output[source] = sorted(targets.values(), key=lambda p: (
        not any(label in directions.values() for label in p['routes']),
        tuple(map(int, p['mapId'].split('/'))),
    ))
    for entry in output[source]:
        assert (root / entry['path'] / 'index.html').is_file(), entry['path']

(root / 'data/location-connections.json').write_text(
    json.dumps(output, ensure_ascii=False, separators=(',', ':'))
)
print('Locations:', len(output), 'destination links:', sum(map(len, output.values())))
print('Connection types and ignored invalid events:', dict(counts))
