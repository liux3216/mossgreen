"""Extract all named, nonempty moves and attach ROM level-up learners."""
import json,struct,sys
from collections import defaultdict
from pathlib import Path
root=Path(__file__).resolve().parent.parent
rom=Path(sys.argv[1]).read_bytes()
chars={bytes.fromhex(k):v for k,v in json.loads((root/'scripts/rom-charmap.json').read_text()).items()}
def word(a):return struct.unpack_from('<I',rom,a&0x1ffffff)[0]
def text(a,n=13):
 data=rom[a&0x1ffffff:][:n];s='';i=0
 while i<len(data) and data[i]!=255:
  key=data[i:i+2]
  if key in chars:s+=chars[key];i+=2
  else:s+=chars.get(data[i:i+1],'�');i+=1
 return s.strip()
names=word(0x148);stats=word(0x1cc)
# Move data occupies 600 twelve-byte records before the name table.
assert names-stats==600*12
types=['一般','格斗','飞行','毒','地面','岩石','虫','幽灵','钢','未知','火','水','草','电','超能力','冰','龙','恶']
pokemon=json.loads((root/'data/pokemon.json').read_text())
growth=json.loads((root/'data/growth.json').read_text())
learners=defaultdict(list)
for sid,info in growth['species'].items():
 p=pokemon[sid];by_move=defaultdict(set)
 for entry in info['learnset']:by_move[entry['move']].add(entry['level'])
 forms=p.get('formIds',[p['id']]);label=p['name']
 if p.get('catalogStatus')=='special-record':label+=' · 毒属性特殊记录'
 elif len(forms)>1:label+=' · 形态 '+str(forms.index(p['id'])+1)
 for mid,levels in by_move.items():learners[mid].append({'id':p['id'],'name':label,'dex':p.get('gameDexId'),'levels':sorted(levels)})
records=[]
for mid in range(1,600):
 name=text(names+13*mid);data=rom[(stats&0x1ffffff)+12*mid:][:12]
 if not name or set(name)<=set('?？'):continue
 category=data[10];typ=data[2]
 assert category in (0,1,2) and (typ<len(types) or typ==23),(mid,name,list(data))
 row={'dataAvailable':any(data),'id':mid,'name':name,'type':types[typ] if typ<len(types) else '妖精','category':['物理','特殊','变化'][category],
 'power':data[1],'accuracy':data[3],'pp':data[4],
 'learners':sorted(learners[mid],key=lambda p:(p['dex'] is None,p['dex'] or 0,p['id']))}
 if str(mid) in growth['moves']:
  for field in ('name','type','category','power','accuracy','pp'):assert row[field]==growth['moves'][str(mid)][field]
 records.append(row)
assert len(records)==576
(root/'data/moves.json').write_text(json.dumps(records,ensure_ascii=False,separators=(',',':')))
print('Extracted',len(records),'moves,',sum(len(r['learners']) for r in records),'learners')
