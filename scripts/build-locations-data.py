"""Build the compact location directory from the atlas's encounter records."""
import json,re
from pathlib import Path
root=Path(__file__).resolve().parent.parent
records=json.loads((root/'data/encounters.json').read_text())
locations={}
for name,map_id,foreign,method,mons in records:
 key=(name,map_id)
 if key not in locations:
  config=re.search(r'（配置 (\d+)）$',name)
  anchor='location-'+map_id.replace('/','-')+('-config-'+config[1] if config else '')
  locations[key]={'name':name,'mapId':map_id,'foreign':foreign,'anchor':anchor,'methods':[],'pokemon':{}}
 location=locations[key]
 if method not in location['methods']:location['methods'].append(method)
 for sid,chance,levels,mon_name in mons:
  if sid and mon_name:location['pokemon'][sid]=mon_name
rows=[]
for location in locations.values():
 rows.append({**location,'pokemon':[{'id':sid,'name':name} for sid,name in location['pokemon'].items()]})
assert not any(row['mapId']=='1/64' for row in rows)
assert next(row for row in rows if row['mapId']=='1/57')['name']=='狩猎地带（分区2）'
(root/'data/locations.json').write_text(json.dumps(rows,ensure_ascii=False,separators=(',',':')))
print('Built',len(rows),'location entries')
