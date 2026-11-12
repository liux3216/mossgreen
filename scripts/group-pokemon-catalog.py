"""Group ROM slots into dex entries while retaining distinct playable forms."""
from base64 import b64decode
from hashlib import sha256
import json
from collections import defaultdict
from pathlib import Path

root = Path(__file__).resolve().parent.parent
path = root / 'data/pokemon.json'
data = json.loads(path.read_text())
overrides = json.loads((root / 'data/pokemon-catalog-overrides.json').read_text())
slots = sorted(data.values(), key=lambda record: record['id'])
duplicate_groups = defaultdict(list)
# The ROM uses these images as placeholders when menu or front artwork is missing.
QUESTION_MARK_ICON = '00d4d1907375eb9cd6ef9ad119a99df21be61d98cbeaf3f51364124da040bbbc'
QUESTION_MARK_SPRITE = '6a212ff718e3e2c879d5230d7da3b922ef965bdd15a1b8a0b332430d92ed4d0f'
for record in slots:
    record.setdefault('sourceLocations', record['locations'])
    for key in ('catalogStatus', 'catalogLabel', 'catalogNote', 'relatedIds'):
        record.pop(key, None)
    record['catalogHidden'] = not any(record['stats'].values()) and record['name'] != '未知图腾'
    record.update(overrides.get(str(record['id']), {}))
    if record['catalogHidden']:
        if record.get('catalogStatus'):
            record.update(canonicalId=record['id'], catalogGroup=None,
                          catalogPrimaryId=record['id'], formIds=[record['id']])
        continue
    icon = record.get('icon')
    sprite = record.get('sprite')
    if sprite and (not icon or sha256(b64decode(icon)).hexdigest() == QUESTION_MARK_ICON):
        if sha256(b64decode(sprite)).hexdigest() != QUESTION_MARK_SPRITE:
            record['icon'] = sprite
    signature = json.dumps([record[key] for key in (
        'gameDexId', 'name', 'stats', 'types', 'abilities', 'catchRate', 'sprite'
    )], sort_keys=True, ensure_ascii=False)
    duplicate_groups[signature].append(record)
canonical = []
for records in duplicate_groups.values():
    first = records[0]
    canonical.append(first)
    places = {}
    for record in records:
        record['canonicalId'] = first['id']
        for place in record['sourceLocations']:
            key = (place['anchor'], place['method'])
            if key not in places:
                places[key] = {**place, 'chance': 0, 'levels': []}
            merged = places[key]
            merged['chance'] += place['chance']
            for level in place['levels']:
                if level not in merged['levels']:
                    merged['levels'].append(level)
    assert all(place['chance'] <= 100 for place in places.values())
    first['locations'] = list(places.values())
numbered = [record for record in canonical if record['gameDexId']]
groups = defaultdict(list)
for record in canonical:
    group = 'dex-' + str(record['gameDexId']) if record['gameDexId'] else None
    if not group:
        candidates = [parent for parent in numbered if parent['name'] == record['name'] or (
            record['nationalId'] and record['nationalId'] == parent['nationalId']
        )]
        group = 'dex-' + str(candidates[0]['gameDexId']) if candidates else 'species-' + str(record['id'])
    groups[group].append(record)
for group, records in groups.items():
    records.sort(key=lambda record: (record['gameDexId'] is None, record['id']))
    form_ids = [record['id'] for record in records]
    for record in records:
        record['catalogGroup'] = group
        record['catalogPrimaryId'] = records[0]['id']
        record['formIds'] = form_ids
for record in slots:
    if not record['catalogHidden'] and record['canonicalId'] != record['id']:
        primary = data[str(record['canonicalId'])]
        for key in ('catalogGroup', 'catalogPrimaryId', 'formIds'):
            record[key] = primary[key]
path.write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':')))
print('Catalog entries:', len(groups), '| numbered dex entries:', len({r['gameDexId'] for r in numbered}))
print('Unique forms:', len(canonical), '| duplicate slots merged:', sum(len(g)-1 for g in duplicate_groups.values()))
