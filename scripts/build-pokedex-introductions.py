"""Match Chinese Pokédex flavor entries by actual species identity, not ROM slot.
Source CSVs are cached outside the published site. Usage: python script.py cache_dir
"""
import csv,json,re,sys,html,urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from collections import defaultdict
root=Path(__file__).resolve().parent.parent;cache=Path(sys.argv[1])
pokemon=json.loads((root/'data/pokemon.json').read_text())
names={};species_names={}
for row in csv.DictReader((cache/'pokemon_species_names.csv').open()):
 if row['local_language_id'] in ('4','12'):
  names[row['name']]=int(row['pokemon_species_id'])
  if row['local_language_id']=='12':species_names[int(row['pokemon_species_id'])]=row['name']
versions={int(r['version_id']):r['name'] for r in csv.DictReader((cache/'version_names.csv').open()) if r['local_language_id']=='12'}
texts={};scores={}
for row in csv.DictReader((cache/'pokemon_species_flavor_text.csv').open()):
 if row['language_id']!='12':continue
 sid=int(row['species_id']);version=int(row['version_id'])
 if version>=scores.get(sid,-1):
  text=re.sub(r'\s+','',row['flavor_text']).strip()
  if text:texts[sid]={'name':species_names.get(sid),'text':text,'version':versions.get(version,'中文'),'source':'https://pokeapi.co/api/v2/pokemon-species/'+str(sid)+'/'};scores[sid]=version
aliases={'谜拟Q':'谜拟丘','负电拍拍':'負电拍拍','属性: 空':'属性：空','多边兽Z':'多边兽乙型','多边兽II':'多边兽２型','流氓熊猫':'霸道熊猫','小智版忍蛙':'甲贺忍蛙'}
def match_name(name):
 name=aliases.get(name,name).replace('·','・')
 if name in names:return names[name]
 stripped=re.sub(r'EX$','',name,flags=re.I)
 if stripped in names:return names[stripped]
 if name.endswith('洛托姆'):return names.get('洛托姆')
 for prefix in ['阿罗拉','超级']:
  if name.startswith(prefix) and name[len(prefix):] in names:return names[name[len(prefix):]]
 return None
matched={key:match_name(p['name']) for key,p in pokemon.items()}
for key,p in pokemon.items():
 if not matched[key] and p.get('catalogPrimaryId'):
  parent=str(p['catalogPrimaryId']);matched[key]=matched.get(parent)
by_species=defaultdict(list)
for key,sid in matched.items():
 p=pokemon[key]
 if sid and any(p['stats'].values()):by_species[sid].append(p)
def rank(p):return ('EX' in p['name'].upper(),p['name']!=species_names.get(matched[str(p['id'])]),p.get('gameDexId') is None,p.get('gameDexId') or 99999,p['id'])
base={sid:sorted(rows,key=rank)[0] for sid,rows in by_species.items()}
# Fill species omitted from the API's Chinese localization using the official Chinese Pokédex.
page_cache=cache/'official-cn';page_cache.mkdir(exist_ok=True)
def official_entry(sid):
 path=page_cache/(str(sid)+'.html')
 try:
  if not path.exists():
   request=urllib.request.Request(f'https://www.pokemon.cn/play/pokedex/{sid:04d}',headers={'User-Agent':'Mozilla/5.0'})
   with urllib.request.urlopen(request,timeout=35) as response:page=response.read().decode('utf-8')
   path.write_text(page)
  else:page=path.read_text()
  matches=re.findall(r'<p[^>]*class="pokemon-story__body[^"<]*"[^>]*>(.*?)</p>',page,re.S)
  descriptions=[re.sub(r'\s+','',html.unescape(re.sub(r'<[^>]+>','',text))) for text in matches]
  descriptions=[text for text in descriptions if text and not text.startswith('{{')]
  if descriptions:return sid,{'name':species_names.get(sid),'text':descriptions[0],'version':'官方中文图鉴','source':f'https://www.pokemon.cn/play/pokedex/{sid:04d}'}
 except Exception as error:print('Unavailable official entry',sid,type(error).__name__,flush=True)
 return sid,None
missing=sorted(set(by_species)-set(texts))
print('Fetching official Chinese entries:',len(missing),flush=True)
with ThreadPoolExecutor(max_workers=6) as pool:
 for sid,entry in pool.map(official_entry,missing):
  if entry:texts[sid]=entry
entries={};used=set()
for key,p in pokemon.items():
 sid=matched[key]
 if sid not in texts:continue
 original=base.get(sid,p)
 special=p['name']!=species_names.get(sid) or p['types']!=original['types'] or p['stats']!=original['stats'] or p['sprite']!=original['sprite']
 entries[key]={'speciesId':sid,'baseDescription':special};used.add(sid)
assert entries['1']['speciesId']==387 and not entries['1']['baseDescription']
assert entries['735']['speciesId']==538 and entries['877']['speciesId']==37
payload={'species':{str(sid):texts[sid] for sid in sorted(used)},'pokemon':entries}
(root/'data/introductions.json').write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':')))
unknown=[p['name'] for key,p in pokemon.items() if key not in entries and any(p['stats'].values()) and p.get('canonicalId')==p['id']]
print('Added introductions for',len(entries),'ROM records from',len(used),'species; unmatched:',unknown)
