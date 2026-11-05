"""Join the wiki's locations with ROM map types, direct connections and atlas cells."""
import json,re,struct,sys
from pathlib import Path
root=Path(__file__).resolve().parent.parent;rom=Path(sys.argv[1]).read_bytes()
def word(a):return struct.unpack_from('<I',rom,a&0x1ffffff)[0]
def raw(a,n):return rom[a&0x1ffffff:][:n]
def header(g,m):return word(word(0x3526a8+g*4)+m*4)&0x1ffffff
atlas=json.loads((root/'data/atlas-locations.json').read_text());maps=json.loads((root/'data/map-layouts.json').read_text())
locations=json.loads((root/'data/locations.json').read_text());by_id={}
for place in locations:by_id.setdefault(place['mapId'],place)
# Native FRLG map types, not inferred from place names.
labels={1:'城镇',2:'城镇',3:'野外',4:'洞穴',5:'水下',6:'水域',8:'室内',9:'室内'}
rows=[]
for place in locations:
 g,m=map(int,place['mapId'].split('/'));hd=header(g,m);kind=raw(hd+23,1)[0];mapdata=maps.get(place['mapId']);cells,note=atlas.get(place['mapId'],[[],'区域图未标出此地点'])
 connections=[];seen=set();cp=word(hd+12)
 if 0x8000000<=cp<0xa000000:
  count,ptr=struct.unpack('<II',raw(cp,8))
  if count<=8 and 0x8000000<=ptr<0xa000000:
   for i in range(count):
    direction=word(ptr+12*i);tg,tm=raw(ptr+12*i+8,2);target=f'{tg}/{tm}'
    if direction not in (1,2,3,4) or target not in by_id or target in seen:continue
    seen.add(target);p=by_id[target];connections.append({'name':p['name'],'mapId':target,'path':'locations/'+p['anchor'].removeprefix('location-')+'/'})
 rows.append({**{k:v for k,v in place.items() if k!='pokemon'},'pokemonCount':len(place['pokemon']),
 'key':place['anchor'].removeprefix('location-'),'type':labels.get(kind,'其他'),'cells':cells,'note':note,
 'path':'locations/'+place['anchor'].removeprefix('location-')+'/',
 'image':'locations/assets/'+place['mapId'].replace('/','-')+'.webp' if mapdata else None,
 'size':mapdata[1:3] if mapdata else None,'connections':connections})
assert not any(p['mapId']=='1/64' for p in rows)
(root/'data/atlas.json').write_text(json.dumps(rows,ensure_ascii=False,separators=(',',':')))
print('Atlas:',len(rows),'locations,',sum(bool(p['cells']) for p in rows),'marked,',sum(len(p['connections']) for p in rows),'direct connections')
