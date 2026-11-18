"""Build independent static location pages and shared map assets from the atlas."""
import base64,hashlib,html,json,re,sys
from pathlib import Path
from wiki_language import add_wiki_language
root=Path(__file__).resolve().parent.parent
records=json.loads((root/'data/encounters.json').read_text())
maps=json.loads((root/'data/map-layouts.json').read_text())
atlas=json.loads((root/'data/atlas-locations.json').read_text())
connections=json.loads((root/'data/location-connections.json').read_text())
locations=json.loads((root/'data/locations.json').read_text())
extra=root/'data/atlas-extra-locations.json'
if extra.exists():locations+=json.loads(extra.read_text())
pokemon=json.loads((root/'data/pokemon.json').read_text())
unavailable_maps=json.loads((root/'data/pokemon-catalog-overrides.json').read_text()).get('unavailableEncounterMaps',{})
special_path=root/'data/special-acquisitions.json'
special=json.loads(special_path.read_text()).get('locations',{}) if special_path.exists() else {}
sprites={key:p['sprite'] for key,p in pokemon.items()}
bykey={}
for name,id,foreign,method,mons in records:bykey.setdefault((name,id),[]).append((method,mons))
directory=(root/'locations/index.html').read_text()
shell=directory[directory.index('<header class="wiki-header">'):directory.index('<main class="pokedex-main">')]
shell=shell.replace('aria-current="page"','aria-current="location"')
if len(sys.argv)>1:
 requested=set(sys.argv[1:])
 unknown=requested-{place['mapId'] for place in locations}
 if unknown:
  raise SystemExit('Unknown map IDs: '+', '.join(sorted(unknown)))
 locations_to_build=[place for place in locations if place['mapId'] in requested]
else:
 locations_to_build=locations
for place in locations_to_build:
 key=place['anchor'].removeprefix('location-')
 methods=[]
 for method,mons in bykey.get((place['name'],place['mapId']),[]):
  values=[]
  for sid,chance,levels,name in mons:
   p=pokemon.get(str(sid));species_id=p.get('canonicalId',sid) if p else sid
   if place['mapId'] in unavailable_maps.get(str(species_id),()):continue
   values.append({'id':sid,'name':name,'chance':chance,'levels':levels,'sprite':sprites.get(str(sid)), 'types':p['types'] if p and all(p['stats'].values()) else [],'known':bool(p and name)})
  methods.append({'name':method,'pokemon':values})
 layout=maps.get(place['mapId']);map_value=None
 if layout:map_value=[layout[0] if layout[0].startswith('locations/') else 'locations/assets/'+place['mapId'].replace('/','-')+'.webp',*layout[1:]]
 base_name=place['name'].split('（')[0]
 related=[{'name':p['name'],'path':'locations/'+p['anchor'].removeprefix('location-')+'/'} for p in locations if p['anchor']!=place['anchor'] and p['name'].split('（')[0]==base_name]
 specials=[{**entry,'pokemonName':pokemon[str(entry['pokemonId'])]['name'],'sprite':pokemon[str(entry['pokemonId'])]['sprite']} for entry in special.get(place['mapId'],[])]
 # The directory keeps the foreign search aliases.
 detail={k:v for k,v in place.items() if k!='foreign'}
 detail.update(methods=methods,map=map_value,atlas=atlas.get(place['mapId']),related=related,connections=connections[place['mapId']],specialAcquisitions=specials)
 if place['mapId']=='1/87':
  detail['waterMap']=json.loads((root/'data/cemetery-water-layout.json').read_text())
 data=root/'locations/data';data.mkdir(exist_ok=True)
 (data/(key+'.json')).write_text(json.dumps(detail,ensure_ascii=False,separators=(',',':')))
 nav_shell=shell
 if not methods:
  nav_shell=shell.replace('href="locations/" aria-current="location"','href="locations/"').replace('href="locations/atlas/"','href="locations/atlas/" aria-current="location"')
 page='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><base href="../../"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>'''+html.escape(place['name'])+''' · 青苔 Wiki</title>
<link rel="stylesheet" href="pokemon.css"><link rel="stylesheet" href="pokemons/list.css"><link rel="stylesheet" href="locations/map-view.css"><link rel="stylesheet" href="locations/detail.css">
<script src="locations/map-view.js" defer></script><script src="locations/detail.js" defer></script></head>
<body class="pokedex-page location-detail-page" data-location="'''+html.escape(key)+'''">'''+nav_shell+'''<main class="pokedex-main">
<h1 id="location-title">'''+html.escape(place['name'])+'''</h1>
<nav class="breadcrumbs" aria-label="当前位置"><a href="./">百科首页</a><span>/</span><a href="locations/">地点分布</a><span>/</span><span aria-current="page">'''+html.escape(place['name'])+'''</span></nav>
<p id="location-status" class="list-status" role="status">正在加载地点资料…</p><article id="location-content" hidden>
<p id="location-meta" class="muted small"></p><div id="location-maps" class="location-maps"></div>
<section class="location-connections" aria-labelledby="connections-heading"><h2 id="connections-heading">相邻地点</h2><nav id="connected-locations" aria-label="相邻地点"></nav><p id="connections-empty" class="muted small" hidden>暂未记录可通往的相邻地点。</p><p id="connections-note" class="muted small" hidden></p></section>
<section id="related-section" class="related-section" hidden><h2>同名地点</h2><nav id="related-locations" aria-label="同名地点"></nav></section>
<section id="special-acquisitions" class="location-special-acquisitions" aria-labelledby="special-acquisitions-heading" hidden><h2 id="special-acquisitions-heading">特殊获取</h2><div class="location-table-wrap"><table class="location-encounter-table"><thead><tr><th scope="col">宝可梦</th><th scope="col">方式</th><th scope="col">等级</th><th scope="col">获取条件</th></tr></thead><tbody id="special-acquisition-rows"></tbody></table></div></section>
<section class="location-encounters" aria-labelledby="encounters-heading"><h2 id="encounters-heading">野生宝可梦</h2>
<div class="filter-fields location-filters"><label class="name-filter" for="encounter-search">查找宝可梦<input id="encounter-search" type="search" placeholder="名称或内部编号" autocomplete="off"></label><label for="encounter-method">遇敌方式<select id="encounter-method"><option value="">全部方式</option></select></label></div>
<div id="location-encounters"></div><p id="encounters-empty" class="empty-state" hidden>没有找到对应的宝可梦。</p></section>
<footer class="list-footer"><p>比例表示该遇敌方式中宝可梦的槽位权重，不是每走一步的遇敌概率。等级与分布取自当前 ROM，剧情变化另有影响。</p><a href="locations/">← 返回地点目录</a></footer></article>
<dialog id="map-dialog" class="map-dialog" aria-labelledby="map-title"><div class="map-toolbar"><h2 id="map-title" class="map-title"></h2><form method="dialog"><button class="map-close">关闭</button></form></div><div id="map-legend" class="map-legend"></div><div id="map-full" class="map-full"></div></dialog>
</main></body></html>'''
 if not methods:
  page=page.replace('<span>/</span><a href="locations/">地点分布</a>','<span>/</span><a href="locations/atlas/">查看地图</a>').replace('<a href="locations/">← 返回地点目录</a>','<a href="locations/atlas/">← 返回查看地图</a>')
 if place['mapId']=='1/61':
  entrance='''<section class="location-connections" aria-labelledby="entrance-heading"><h2 id="entrance-heading">怎么进入</h2>
<p><strong>左上房间（主线）</strong>。从<a href="locations/3-35/">普里皮亚特镇</a>进入<a href="locations/1-59/">核电站南口入口区</a>，往左走到两个书架之间的灰色门（5, 27），继续按上。若安保机器人挡门，先去<a href="locations/1-60/">分区 2</a>调查左上方的书架（7, 9），找到密码「紫色」，再回南口与机器人对话并击败它。</p>
<p><strong>反应堆房间（支线）</strong>。向 Morgana 接取<a href="walkthrough/#illuminati-8">光明会任务八「重建普里皮亚特」</a>，回到分区 2，从左上方的灰色门（4, 1）进入。击败门前的机器人后，楼梯会把你送到分区 3 的下方房间。</p>
<p>三个控制面板依次在（30, 42）、（71, 33）和（68, 2）。关掉第一块后，沿原路回到下方入口房间，走（53, 65）的门。关掉第二块后再回到入口房间，走（48, 65）的门。</p></section>'''
  page=page.replace('<section class="location-connections" aria-labelledby="connections-heading">',entrance+'\n<section class="location-connections" aria-labelledby="connections-heading">',1)
 if place['mapId']=='1/87':
  water_layout='''<section class="location-map-card" aria-labelledby="water-layout-heading"><h2 id="water-layout-heading">水域示意图</h2>
<div id="water-layout-preview"></div>
<p>点击放大，可切换遇敌格高亮。</p>
<p>完成德拉科·马尔福的基拉祈事件后，游戏会在载入地图时切换为水域地形。冲浪和钓鱼记录适用于水域地形。</p></section>'''
  page=page.replace('</div>\n<section class="location-connections" aria-labelledby="connections-heading">','</div>\n'+water_layout+'\n<section class="location-connections" aria-labelledby="connections-heading">',1)
 for asset in ['pokemon.css','pokemons/list.css','locations/map-view.css','locations/detail.css','locations/map-view.js','locations/detail.js']:
  page=page.replace('"'+asset+'"','"'+asset+'?v='+hashlib.sha256((root/asset).read_bytes()).hexdigest()[:12]+'"')
 destination=root/'locations'/key;destination.mkdir(exist_ok=True);(destination/'index.html').write_text(add_wiki_language(page))
print('Built',len(locations_to_build),'location detail pages')
