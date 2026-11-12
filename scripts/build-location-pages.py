"""Build independent static location pages and shared map assets from the atlas."""
import base64,hashlib,html,json,re
from pathlib import Path
root=Path(__file__).resolve().parent.parent
records=json.loads((root/'data/encounters.json').read_text())
maps=json.loads((root/'data/map-layouts.json').read_text())
atlas=json.loads((root/'data/atlas-locations.json').read_text())
connections=json.loads((root/'data/location-connections.json').read_text())
locations=json.loads((root/'data/locations.json').read_text())
extra=root/'data/atlas-extra-locations.json'
if extra.exists():locations+=json.loads(extra.read_text())
pokemon=json.loads((root/'data/pokemon.json').read_text())
special_path=root/'data/special-acquisitions.json'
special=json.loads(special_path.read_text()).get('locations',{}) if special_path.exists() else {}
sprites={key:p['sprite'] for key,p in pokemon.items()}
bykey={}
for name,id,foreign,method,mons in records:bykey.setdefault((name,id),[]).append((method,mons))
directory=(root/'locations/index.html').read_text()
shell=directory[directory.index('<header class="wiki-header">'):directory.index('<main class="pokedex-main">')]
shell=shell.replace('aria-current="page"','aria-current="location"')
for place in locations:
 key=place['anchor'].removeprefix('location-')
 methods=[]
 for method,mons in bykey.get((place['name'],place['mapId']),[]):
  values=[]
  for sid,chance,levels,name in mons:
   p=pokemon.get(str(sid));values.append({'id':sid,'name':name,'chance':chance,'levels':levels,'sprite':sprites.get(str(sid)), 'types':p['types'] if p and all(p['stats'].values()) else [],'known':bool(p and name)})
  methods.append({'name':method,'pokemon':values})
 layout=maps.get(place['mapId']);map_value=None
 if layout:map_value=[layout[0] if layout[0].startswith('locations/') else 'locations/assets/'+place['mapId'].replace('/','-')+'.webp',*layout[1:]]
 base_name=place['name'].split('（')[0]
 related=[{'name':p['name'],'path':'locations/'+p['anchor'].removeprefix('location-')+'/'} for p in locations if p['anchor']!=place['anchor'] and p['name'].split('（')[0]==base_name]
 specials=[{**entry,'pokemonName':pokemon[str(entry['pokemonId'])]['name'],'sprite':pokemon[str(entry['pokemonId'])]['sprite']} for entry in special.get(place['mapId'],[])]
 detail={**place,'methods':methods,'map':map_value,'atlas':atlas.get(place['mapId']),'related':related,'connections':connections[place['mapId']],'specialAcquisitions':specials}
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
 for asset in ['pokemon.css','pokemons/list.css','locations/map-view.css','locations/detail.css','locations/map-view.js','locations/detail.js']:
  page=page.replace('"'+asset+'"','"'+asset+'?v='+hashlib.sha256((root/asset).read_bytes()).hexdigest()[:12]+'"')
 destination=root/'locations'/key;destination.mkdir(exist_ok=True);(destination/'index.html').write_text(page)
print('Built',len(locations),'location detail pages')
