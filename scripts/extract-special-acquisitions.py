"""Extract NPC gifts, eggs, fixed wild encounters, exchanges and prize Pokémon.

Usage: python3 scripts/extract-special-acquisitions.py game.gba [audit.json]
Only map-attached events with a resolvable real species are published. The audit
keeps addresses/branch metadata; player-facing data contains acquisition details.
"""
from pathlib import Path
from collections import defaultdict,Counter
import hashlib,json,re,struct,sys
from rom_field_scripts import FieldScripts

root=Path(__file__).resolve().parent.parent
rom=Path(sys.argv[1]).read_bytes();scripts=FieldScripts(rom,root)
pokemon=json.loads((root/'data/pokemon.json').read_text())
places={}
for p in json.loads((root/'data/atlas.json').read_text()):places.setdefault(p['mapId'],p)
overrides=json.loads((root/'data/special-acquisition-overrides.json').read_text())
word,half,byte=scripts.word,scripts.half,scripts.byte
assert word(0x53ad4)==0x0826cf8c
trades=[]
for i in range(9):
 a=0x826cf8c+60*i
 trades.append({'species':half(a+12),'requestedSpecies':half(a+56)})
items=word(0x1c8)
def item_name(i):return scripts.text(items+44*i,14) if 0<i<375 else '道具 #'+str(i)
def species_name(i):return pokemon.get(str(i),{}).get('name','宝可梦 #'+str(i))
def resolve(value,variables):return value if value<0x4000 else variables.get(value)
def classify(features,kind):
 if kind=='trade':return 'NPC交换'
 if kind=='egg':return '赠蛋'
 if kind=='static':return '固定遭遇'
 if features['coins']:return '代币兑换'
 if features['money']:return '购买宝可梦'
 if features['battle'] or features['random']:return '事件奖励'
 return 'NPC赠送'

rows={};audit=[];limited=[];unresolved=[];entrances=defaultdict(list)
walks={};features_by_root={}
for start,origins in scripts.roots.items():
 if not any(o['mapId'] in places for o in origins):continue
 walk=scripts.walk(start);walks[start]=walk
 ops={scripts.node(p)['op'] for p in walk}
 texts=[scripts.text(word(p+2)) for p in walk if scripts.node(p)['op']==15 and byte(p+1)==0]
 features_by_root[start]={'battle':0x5c in ops,'random':0x8f in ops,'coins':0xb5 in ops,'money':0x91 in ops,'texts':texts}
 # A hidden entrance may be a script warp rather than a physical door.
 for p in walk:
  if scripts.node(p)['op'] not in (0x39,0x3a,0x3b,0x3c,0x3d,0xd1):continue
  key=f'{byte(p+1)}/{byte(p+2)}'
  if key not in places:continue
  dig=any(scripts.node(q)['op']==0x7c and half(q+1)==91 for q in walk)
  for origin in origins:
   source=places.get(origin['mapId'])
   if not source or source['mapId']==key:continue
   entry={'name':source['name'].strip() or '地图 '+source['mapId'],'path':source['path'],'method':'挖洞' if dig else '事件入口'}
   if entry not in entrances[key]:entrances[key].append(entry)

def record(sid,level,kind,pc,start,variables,notes,origins,trade=None):
 if sid is None or not 0<sid<1304 or str(sid) not in pokemon:
  unresolved.append({'instruction':hex(pc),'species':sid,'root':hex(start)});return
 p=pokemon[str(sid)]
 if not any(p['stats'].values()):return
 canonical=p.get('canonicalId',sid);method=classify(features_by_root[start],kind)
 for origin in origins:
  place=places.get(origin['mapId'])
  if not place:continue
  condition=[]
  if kind=='static':condition.append('与宝可梦互动触发战斗，需自行捕捉。')
  elif kind=='egg':condition.append('完成对应剧情后领取蛋，再孵化获得。')
  elif kind=='trade':condition.append('用'+species_name(trade['requestedSpecies'])+'交换。')
  elif method=='代币兑换':
   price=variables.get(0x4002)
   condition.append(('需要 '+str(price)+' 枚代币。') if price else '使用游戏代币兑换。')
  elif method=='购买宝可梦':condition.append('与此处 NPC 交谈并支付费用。')
  elif (0,-1) in notes:condition.append('完成此处的训练家战斗后领取。')
  else:condition.append('与此处 NPC 交谈领取。' if origin['kind']=='npc' else '完成此处剧情后获得。')
  if features_by_root[start]['random'] and kind=='gift':condition.append('此事件的奖励池包含这只宝可梦。')
  for item,count in notes:
   if item and count:condition.append('需要'+item_name(item)+(' × '+str(count) if count>1 else '')+'。')
  key=(canonical,place['mapId'],method,trade['requestedSpecies'] if trade else None)
  if key not in rows:
   rows[key]={'pokemonId':canonical,'sourceSpeciesIds':[],'name':place['name'].strip() or '地图 '+place['mapId'],'mapId':place['mapId'],'path':place['path'],'anchor':place['anchor'],'method':method,'kind':kind,'levels':[],'conditions':[],'origins':[],'entrances':entrances.get(place['mapId'],[])}
  entry=rows[key]
  if sid not in entry['sourceSpeciesIds']:entry['sourceSpeciesIds'].append(sid)
  if level and 0<level<=100 and [level,level] not in entry['levels']:entry['levels'].append([level,level])
  if kind=='trade':entry['levelNote']='与交出的宝可梦等级相同';entry['requestedSpeciesId']=trade['requestedSpecies']
  elif kind=='egg':entry['levels']=[[5,5]];entry['levelNote']='孵化后 Lv.5'
  elif level==0:entry['levelNote']='等级待核实'
  for text in condition:
   if text not in entry['conditions']:entry['conditions'].append(text)
  o={k:v for k,v in origin.items() if k in ('kind','localId','x','y')}
  if o not in entry['origins']:entry['origins'].append(o)
  evidence={'instruction':hex(pc),'root':hex(start),'species':sid,'mapId':place['mapId'],'method':method,'origin':origin,'variables':{hex(k):v for k,v in variables.items()},'texts':features_by_root[start]['texts']}
  audit.append(evidence)

for start,walk in walks.items():
 interesting=any(scripts.node(p)['op'] in (0x79,0x7a,0xb7) or scripts.node(p)['op']==0x25 and half(p+1)==253 for p in walk)
 if not interesting:continue
 origins=scripts.roots[start]
 # State: pc, return stack, known variables, latest comparison, prepared wild
 # encounter, and item requirements. Values unknown to static analysis stay unset.
 todo=[(start,(),(),None,None,())];seen=set();steps=0
 while todo and steps<30000:
  pc,stack,frozen,comparison,wild,notes=todo.pop();variables=dict(frozen)
  while scripts.valid(pc) and steps<30000:
   state=(pc,stack,tuple(sorted(variables.items())),comparison,wild,notes)
   if state in seen:break
   seen.add(state);steps+=1;n=scripts.node(pc);op=n['op']
   if not n['size']:break
   nxt=pc+n['size'];get=lambda v:resolve(v,variables)
   if op in (0x16,0x17,0x18,0x19,0x1a):
    var,value=half(pc+1),half(pc+3)
    if op==0x19:value=variables.get(value)
    elif op==0x1a:value=get(value)
    elif op in (0x17,0x18):
     previous=variables.get(var);value=None if previous is None else (previous+value if op==0x17 else previous-value)&65535
    if value is None:variables.pop(var,None)
    else:variables[var]=value
   elif op in (0x21,0x22):comparison=(half(pc+1),get(half(pc+3)) if op==0x22 else half(pc+3))
   elif op in (0x2b,0x27):comparison=None
   elif op in (0x25,0x26):
    special=half(pc+(1 if op==0x25 else 3));dest=half(pc+1) if op==0x26 else 0x800d
    variables.pop(dest,None)
    if special==252:
     index=variables.get(0x8004)
     if index is not None and 0<=index<len(trades):variables[dest]=trades[index]['requestedSpecies']
    elif special==253:
     index=variables.get(0x8004)
     if index is not None and 0<=index<len(trades):
      trade=trades[index];record(trade['species'],None,'trade',pc,start,variables,notes,origins,trade)
     else:unresolved.append({'instruction':hex(pc),'tradeIndex':index,'root':hex(start)})
   elif op in (0x6e,0x6f,0x70,0x71,0x8f,0xb3,0x43):variables.pop(0x800d,None);comparison=None
   elif op in (0x45,0x47):
    item,count=get(half(pc+1)),get(half(pc+3))
    if op==0x45 and item and count and (item,count) not in notes:notes=notes+((item,count),)
    variables.pop(0x800d,None)
   elif op==0x5c:
    if (0,-1) not in notes:notes=notes+((0,-1),)
    for target in n['next']:
     if target!=nxt:todo.append((target,stack,tuple(sorted(variables.items())),comparison,wild,notes))
   elif op in (0x79,0x7a):
    record(get(half(pc+1)),byte(pc+3) if op==0x79 else 5,'gift' if op==0x79 else 'egg',pc,start,variables,notes,origins)
    variables.pop(0x800d,None);comparison=None
   elif op==0xb6:wild=(get(half(pc+1)),byte(pc+3))
   elif op==0xb7:
    if wild:record(wild[0],wild[1],'static',pc,start,variables,notes,origins)
    wild=None
   if op in (2,0x0d,0x24):break
   if op==3:
    if not stack:break
    pc=stack[-1];stack=stack[:-1];continue
   if op in (4,5):
    target=word(pc+1)
    if not scripts.valid(target) or len(stack)>=12:break
    if op==4:stack=stack+(nxt,)
    pc=target;continue
   if op in (8,9,10,11):
    index=byte(pc+(1 if op in (8,9) else 2))
    if index>=10:break
    target=word(0x8160450+4*index)
    if op in (10,11):todo.append((target,stack+((nxt,) if op==11 else ()),tuple(sorted(variables.items())),comparison,wild,notes));pc=nxt;continue
    if op==9:stack=stack+(nxt,)
    pc=target;continue
   if op in (6,7):
    condition=byte(pc+1);target=word(pc+2);known=None
    if comparison:
     var,value=comparison;current=variables.get(var)
     if current is not None and value is not None:known=[current<value,current==value,current>value,current<=value,current>=value,current!=value][condition] if condition<6 else None
    if known is not False and scripts.valid(target) and len(stack)<12:
     branch=dict(variables)
     if comparison and condition==1 and comparison[1] is not None:branch[comparison[0]]=comparison[1]
     todo.append((target,stack+((nxt,) if op==7 else ()),tuple(sorted(branch.items())),comparison,wild,notes))
    if known is True:break
   pc=nxt
 if todo:limited.append({'root':hex(start),'origins':origins,'states':steps})

records=[]
for entry in rows.values():
 # Curated explanations can refine a verified event, never invent a new source.
 key=str(entry['pokemonId'])+'@'+entry['mapId']
 if key in overrides.get('entries',{}):entry.update(overrides['entries'][key])
 entry['levels'].sort();records.append(entry)
records.sort(key=lambda e:(e['pokemonId'],tuple(map(int,e['mapId'].split('/'))),e['method']))
by_pokemon=defaultdict(list);by_location=defaultdict(list)
for i,entry in enumerate(records):
 entry['id']='special-'+str(i+1)
 by_pokemon[str(entry['pokemonId'])].append(entry);by_location[entry['mapId']].append(entry)
summary={'records':len(records),'pokemon':len(by_pokemon),'maps':len(by_location),'methods':dict(Counter(e['method'] for e in records))}
payload={'schemaVersion':1,'summary':summary,'pokemon':dict(by_pokemon),'locations':dict(by_location)}
(root/'data/special-acquisitions.json').write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':')))
audit_path=Path(sys.argv[2]) if len(sys.argv)>2 else Path('/tmp/mossgreen-special-acquisitions-audit.json')
audit_path.write_text(json.dumps({'romSha256':hashlib.sha256(rom).hexdigest(),'mapsScanned':len(scripts.maps),'scriptRoots':len(scripts.roots),'parsedInstructions':len(scripts.nodes),'summary':summary,'limitedRoots':limited,'unknownOpcodes':{hex(k):v for k,v in scripts.unknown.items()},'unresolvedSpeciesOrTrades':unresolved,'sources':audit},ensure_ascii=False,indent=2))
assert any(e['pokemonId']==142 and e['mapId']=='1/8' and e['method']=='固定遭遇' for e in records)
print(json.dumps(summary,ensure_ascii=False));print('Unresolved:',len(unresolved),'limited roots:',len(limited),'unknown instructions:',len(scripts.unknown))
