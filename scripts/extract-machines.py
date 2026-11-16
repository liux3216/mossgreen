# -*- coding: utf-8 -*-
"""Extract live TM/HM mapping, compatibility and map-attached item sources.
Usage: python scripts/extract-machines.py game.gba
A previous unreferenced TM table remains in this ROM; use the live function's pointer.
"""
import json,struct,sys
from pathlib import Path
from rom_item_sources import collect_item_sources
root=Path(__file__).resolve().parent.parent
rom=Path(sys.argv[1]).read_bytes();pokedex=json.loads((root/'data/pokemon.json').read_text())
move_data={v['id']:v for v in json.loads((root/'data/moves.json').read_text())}
places={v['mapId']:v for v in json.loads((root/'data/atlas.json').read_text())}
def off(a):return a&0x1ffffff
def word(a):return struct.unpack_from('<I',rom,off(a))[0]
def half(a):return struct.unpack_from('<H',rom,off(a))[0]
def byte(a):return rom[off(a)]
moves=word(0x125a8c);compat=word(0x43c68)
assert moves==0x0845a80c and compat==word(0x43c80)==0x08c4de80
assert [half(moves+2*i) for i in [0,7,50,54,55]]==[524,73,15,91,249]
items=word(0x1c8);machine_ids=set(range(289,347))
assert all(half(items+i*44+14)==i and byte(items+i*44+26)==4 for i in machine_ids)
assert {i for i in range(1,375) if byte(items+i*44+26)==4}==machine_ids
sources, audit = collect_item_sources(rom, root, places, machine_ids)

rows=[]
for index,item in enumerate(range(289,347)):
 code=f'TM{index+1:02}' if index<50 else f'HM{index-49:02}'
 mid=half(moves+index*2);move=move_data[mid]
 learners=[]
 for p in pokedex.values():
  if p.get('catalogHidden') or p.get('canonicalId')!=p['id'] or not all(p['stats'].values()):continue
  mask=struct.unpack_from('<Q',rom,off(compat)+p['id']*8)[0]
  if mask&(1<<index):learners.append(p['id'])
 learners.sort(key=lambda sid:(pokedex[str(sid)].get('gameDexId') or 99999,sid))
 row={'id':code,'kind':code[:2],'number':index+1 if index<50 else index-49,'itemId':item,'moveId':mid,**{k:move[k] for k in ['name','type','category','power','accuracy','pp']},'learners':learners,'locations':sorted(sources[item].values(),key=lambda p:(p['name'],p['method']))}
 rows.append(row)
assert len(rows)==58 and rows[54]['name']=='挖洞' and rows[0]['name']=='真气弹'
(root/'data/machines.json').write_text(json.dumps(rows,ensure_ascii=False,separators=(',',':')))
Path('/tmp/mossgreen-machines-audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2))
print('Machines:',len(rows),'TM:',50,'HM:',8,'with sources:',sum(bool(r['locations']) for r in rows),'map/method sources:',sum(len(r['locations']) for r in rows),'script roots:',audit['roots'],'limited:',audit['limitedRoots'])
for row in rows:
 print(row['id'],row['name'],'learners',len(row['learners']),'sources',[(p['name'],p['method']) for p in row['locations']])
