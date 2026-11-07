# -*- coding: utf-8 -*-
"""Extract live TM/HM mapping, compatibility and map-attached item sources.
Usage: python scripts/extract-machines.py game.gba
A previous unreferenced TM table remains in this ROM; use the live function's pointer.
"""
import json,struct,sys,collections
from pathlib import Path
root=Path(__file__).resolve().parent.parent
rom=Path(sys.argv[1]).read_bytes();pokedex=json.loads((root/'data/pokemon.json').read_text())
move_data={v['id']:v for v in json.loads((root/'data/moves.json').read_text())}
places={v['mapId']:v for v in json.loads((root/'data/atlas.json').read_text())}
commands=json.loads((root/'scripts/field-script-opcodes.json').read_text());widths={int(k):v for k,v in commands['lengths'].items()}
def off(a):return a&0x1ffffff
def word(a):return struct.unpack_from('<I',rom,off(a))[0]
def half(a):return struct.unpack_from('<H',rom,off(a))[0]
def byte(a):return rom[off(a)]
def valid(a):return 0x8000000<=a<0xa000000
moves=word(0x125a8c);compat=word(0x43c68)
assert moves==0x0845a80c and compat==word(0x43c80)==0x08c4de80
assert [half(moves+2*i) for i in [0,7,50,54,55]]==[524,73,15,91,249]
items=word(0x1c8);machine_ids=set(range(289,347))
assert all(half(items+i*44+14)==i and byte(items+i*44+26)==4 for i in machine_ids)
assert {i for i in range(1,375) if byte(items+i*44+26)==4}==machine_ids
sources=collections.defaultdict(dict);audit=[];unknown=collections.Counter();root_count=0;limited=0

def record(item,map_id,kind,origin,address):
 if item not in machine_ids:return
 place=places[map_id];key=(map_id,kind)
 # Keep one listing per map/method; the audit preserves every attached script.
 sources[item][key]={'name':place['name'],'mapId':map_id,'path':place['path'],'method':kind}
 audit.append({'item':item,'mapId':map_id,'method':kind,'origin':origin,'instruction':hex(address)})

def follow(start,map_id,origin):
 global root_count,limited
 if not valid(start):return
 root_count+=1;todo=[(start,(),())];seen=set();steps=0
 while todo and steps<2000:
  pc,stack,frozen=todo.pop();variables=dict(frozen)
  while valid(pc) and steps<2000:
   key=(pc,stack,tuple(sorted(variables.items())))
   if key in seen:break
   seen.add(key);steps+=1;op=byte(pc);n=widths.get(op)
   if op==0x5c:
    mode=byte(pc+1);n={0:14,1:18,2:18,3:10,4:18,5:14,6:22,7:18,8:22,9:14}.get(mode)
    if mode in [1,2,6,8]:
     dest=word(pc+n-4)
     if valid(dest):todo.append((dest,stack,tuple(sorted(variables.items()))))
   if n is None or n<1:
    unknown[op]+=1;break
   nxt=pc+n
   get=lambda v: v if v<0x4000 else variables.get(v)
   if op in (0x16,0x17,0x18,0x19,0x1a):
    var,value=half(pc+1),half(pc+3)
    if op==0x19:value=variables.get(value)
    elif op==0x1a:value=get(value)
    elif op in (0x17,0x18):
     current=variables.get(var);value=None if current is None else (current+value if op==0x17 else current-value)&65535
    if value is None:variables.pop(var,None)
    else:variables[var]=value
   elif op in (0x08,0x09,0x0a,0x0b):
    std=byte(pc+1 if op in (0x08,0x09) else pc+2)
    if std in (0,1):record(variables.get(0x8000),map_id,'地面拾取' if std==1 else 'NPC赠送／事件奖励',origin,pc)
    if op==0x08:break
   elif op==0x44:record(get(half(pc+1)),map_id,'NPC赠送／事件奖励',origin,pc)
   elif op==0x86:
    shop=word(pc+1)
    if valid(shop):
     for i in range(128):
      item=half(shop+2*i)
      if item==0:break
      if item>=375:break
      record(item,map_id,'商店购买',origin,pc)
   if op in (2,0x0d):break
   if op==3:
    if not stack:break
    pc=stack[-1];stack=stack[:-1];continue
   if op in (4,5):
    target=word(pc+1)
    if not valid(target) or len(stack)>=8:break
    if op==4:stack=stack+(nxt,)
    pc=target;continue
   if op in (6,7):
    target=word(pc+2)
    if valid(target) and len(stack)<8:todo.append((target,stack+((nxt,) if op==7 else ()),tuple(sorted(variables.items()))))
   pc=nxt
 if steps>=2000:limited+=1

for map_id,place in places.items():
 group,number=map(int,map_id.split('/'));header=word(word(0x3526a8+group*4)+number*4)
 if not valid(header):continue
 events=word(header+4)
 if not valid(events):continue
 counts=[byte(events+i) for i in range(4)];objects=word(events+4)
 if valid(objects):
  for i in range(counts[0]):follow(word(objects+i*24+16),map_id,'object:'+str(i))
 coords=word(events+12)
 if valid(coords):
  for i in range(counts[2]):follow(word(coords+i*16+12),map_id,'coord:'+str(i))
 background=word(events+16)
 if valid(background):
  for i in range(counts[3]):
   entry=background+i*12;kind=byte(entry+5)
   if kind==7:record(half(entry+8),map_id,'隐藏道具','background:'+str(i),entry)
   elif kind<=4:follow(word(entry+8),map_id,'background:'+str(i))
 scripts=word(header+8)
 if valid(scripts):
  for i in range(30):
   kind=byte(scripts+i*5)
   if not kind:break
   ptr=word(scripts+i*5+1)
   if not valid(ptr):continue
   if kind in [2,4]:
    for j in range(64):
     if half(ptr+j*8)==0:break
     follow(word(ptr+j*8+4),map_id,'map-condition:'+str(i))
   else:follow(ptr,map_id,'map-script:'+str(i))

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
Path('/tmp/mossgreen-machines-audit.json').write_text(json.dumps({'roots':root_count,'limitedRoots':limited,'unknownOpcodes':dict(unknown),'sources':audit},ensure_ascii=False,indent=2))
print('Machines:',len(rows),'TM:',50,'HM:',8,'with sources:',sum(bool(r['locations']) for r in rows),'map/method sources:',sum(len(r['locations']) for r in rows),'script roots:',root_count,'limited:',limited)
for row in rows:
 print(row['id'],row['name'],'learners',len(row['learners']),'sources',[(p['name'],p['method']) for p in row['locations']])
