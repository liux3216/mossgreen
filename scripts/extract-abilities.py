"""Extract ROM ability names/descriptions and join holders and wild locations."""
import json,struct,sys
from collections import defaultdict
from pathlib import Path
root=Path(__file__).resolve().parent.parent
rom=Path(sys.argv[1]).read_bytes()
chars={bytes.fromhex(k):v for k,v in json.loads((root/'scripts/rom-charmap.json').read_text()).items()}
def word(a):return struct.unpack_from('<I',rom,a&0x1ffffff)[0]
def text(a,n=250):
 data=rom[a&0x1ffffff:][:n];out='';i=0
 while i<len(data) and data[i]!=255:
  key=data[i:i+2]
  if key in chars:out+=chars[key];i+=2
  else:out+=chars.get(data[i:i+1],'�');i+=1
 return out.strip()
names=word(0x1c0);descriptions=word(0x1c4)
assert names-descriptions==78*4
pokemon=json.loads((root/'data/pokemon.json').read_text())
holders=defaultdict(list);locations=defaultdict(dict)
for p in pokemon.values():
 if p.get('canonicalId')!=p['id'] or not all(p['stats'].values()):continue
 forms=p.get('formIds',[p['id']]);label=p['name']
 if p.get('catalogStatus')=='special-record':label+=' · 毒属性特殊记录'
 elif len(forms)>1:label+=' · 形态 '+str(forms.index(p['id'])+1)
 for a in p['abilities']:
  holders[a['id']].append({'id':p['id'],'name':label,'dex':p.get('gameDexId')})
  for place in p['locations']:
   key=(place['anchor'],place['method']);entries=locations[a['id']]
   if key not in entries:entries[key]={k:place[k] for k in ('name','mapId','anchor','method')};entries[key]['holders']=set()
   entries[key]['holders'].add(p['id'])
rows=[]
for aid in range(1,78):
 name=text(names+13*aid,13);ptr=word(descriptions+4*aid)
 assert 0x8000000<=ptr<0xa000000 and name
 description=text(ptr);assert description and '�' not in description and '{' not in description
 places=[]
 for place in locations[aid].values():places.append({**{k:v for k,v in place.items() if k!='holders'},'pokemonCount':len(place['holders'])})
 rows.append({'id':aid,'name':name,'description':description,
 'pokemon':sorted(holders[aid],key=lambda p:(p['dex'] is None,p['dex'] or 0,p['id'])),
 'locations':sorted(places,key=lambda p:(p['name'],p['mapId'],p['method']))})
assert len({r['name'] for r in rows})==len(rows)
assert rows[21]['name']=='威吓' and rows[21]['description']=='降低对手攻击'
for p in pokemon.values():
 if p.get('canonicalId')==p['id'] and all(p['stats'].values()):
  for a in p['abilities']:assert rows[a['id']-1]['name']==a['name']
(root/'data/abilities.json').write_text(json.dumps(rows,ensure_ascii=False,separators=(',',':')))
print('Extracted',len(rows),'abilities,',sum(len(r['pokemon']) for r in rows),'holder records')
