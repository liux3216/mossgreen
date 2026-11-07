"""Extract this ROM's five-slot evolutions and expanded three-byte learnsets.
Usage: python3 scripts/extract-pokemon-growth.py /path/to/game.gba
No ROM is copied into the website.
"""
import json,struct,sys
from pathlib import Path
root=Path(__file__).resolve().parent.parent
rom=Path(sys.argv[1]).read_bytes()
chars={bytes.fromhex(k):v for k,v in json.loads((root/'scripts/rom-charmap.json').read_text()).items()}
def word(a):return struct.unpack_from('<I',rom,a&0x1ffffff)[0]
def half(a):return struct.unpack_from('<H',rom,a&0x1ffffff)[0]
def raw(a,n):return rom[a&0x1ffffff:][:n]
def text(a,n=13):
 data=raw(a,n);out='';i=0
 while i<len(data) and data[i]!=255:
  key=data[i:i+2]
  if key in chars:out+=chars[key];i+=2
  else:out+=chars.get(data[i:i+1],'�');i+=1
 return out.strip()
# Tables verified against the active evolution routine and learnset ASM hook.
evolutions=word(0x42fbc)
learnsets=word(0xa3d66c)
move_names=word(0x148);move_stats=word(0x1cc);items=word(0x1c8)
assert evolutions==0x8c51138 and learnsets==0x8b65080
pokemon=json.loads((root/'data/pokemon.json').read_text())
types=['一般','格斗','飞行','毒','地面','岩石','虫','幽灵','钢','未知','火','水','草','电','超能力','冰','龙','恶']
def item(n):return text(items+44*n) or f'道具 #{n}'
def condition(method,param):
 return {
 1:'亲密度达到 220 后升级',2:'白天亲密度达到 220 后升级',3:'夜间亲密度达到 220 后升级',
 4:f'Lv.{param}',5:'连接交换',6:f'携带{item(param)}连接交换',7:f'使用{item(param)}',
 8:f'Lv.{param}，攻击＞防御',9:f'Lv.{param}，攻击＝防御',10:f'Lv.{param}，攻击＜防御',
 11:f'Lv.{param} 起升级；隐藏性格值高 16 位的十进制个位为 0–4',
 12:f'Lv.{param} 起升级；隐藏性格值高 16 位的十进制个位为 5–9',13:f'Lv.{param}',
 14:f'Lv.{param}，队伍有空位且背包有精灵球',15:f'美丽度达到 {param} 后升级'
 }[method]
def canonical(n):
 p=pokemon.get(str(n));return p.get('canonicalId',n) if p else n
species={};moves={};edges=[];seen=set()
for key,p in pokemon.items():
 sid=int(key)
 if not any(p['stats'].values()) or p.get('canonicalId')!=sid:continue
 entry={'learnset':[],'evolutions':[],'invalidLearnset':False,'invalidEvolution':False}
 for slot in range(5):
  method,param,target,_=struct.unpack('<4H',raw(evolutions+40*sid+8*slot,8))
  if not method:continue
  target=canonical(target)
  if method not in range(1,16) or str(target) not in pokemon or not any(pokemon[str(target)]['stats'].values()):
   entry['invalidEvolution']=True;continue
  edge={'from':sid,'to':target,'method':method,'param':param,'condition':condition(method,param)}
  identity=(sid,target,method,param)
  if identity not in seen:entry['evolutions'].append(edge);seen.add(identity)
 # A damaged row can contain bytes that coincidentally resemble a valid edge.
 # Keep the row flagged for review instead of publishing a partial evolution.
 if entry['invalidEvolution']:entry['evolutions']=[]
 else:edges.extend(entry['evolutions'])
 if any(edge['method'] in (11,12) for edge in entry['evolutions']):
  entry['evolutionNotes']=['这里的「性格值」是隐藏的个体编号，与「固执、胆小」等性格无关。取它的高 16 位，转成十进制后看个位数：0–4 对应甲壳茧，5–9 对应盾甲茧，两种分支各约 50%。分支在个体生成时就已固定，同一只刺尾虫读档重试或改变升级时间都不会改变结果；想获得另一条进化路线，需要捕获或孵化不同的刺尾虫。']
 ptr=word(learnsets+4*sid)
 if not 0x8000000<=ptr<0xa000000:entry['invalidLearnset']=True
 else:
  for slot in range(128):
   data=raw(ptr+3*slot,3);mid=int.from_bytes(data[:2],'little');level=data[2]
   if level==255:break
   if not 0<mid<600 or not 0<level<=100:entry['invalidLearnset']=True;continue
   entry['learnset'].append({'level':level,'move':mid})
   if str(mid) not in moves:
    data=raw(move_stats+12*mid,12);typ=data[2];category=data[10]
    moves[str(mid)]={'name':text(move_names+13*mid),'type':types[typ] if typ<len(types) else '妖精' if typ==23 else f'属性 #{typ}', 'category':['物理','特殊','变化'][category] if category<3 else '待核实','power':data[1],'accuracy':data[3],'pp':data[4]}
  else:entry['invalidLearnset']=True
 species[key]=entry
payload={'species':species,'moves':moves,'evolutions':edges}
(root/'data/growth.json').write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':')))
assert species['1']['evolutions'][0]['to']==2 and species['1']['evolutions'][0]['param']==18
assert species['2']['evolutions'][0]['to']==3 and species['2']['evolutions'][0]['param']==32
assert species['1']['learnset'][0]=={'level':1,'move':33}
assert moves['33']['name']=='撞击' and moves['33']['category']=='物理'
print(f'Extracted {len(species)} forms, {len(edges)} evolution edges and {len(moves)} moves')
