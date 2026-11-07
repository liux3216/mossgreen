# -*- coding: utf-8 -*-
"""Build the machine catalog using the same sidebar and layout as the wiki."""
from pathlib import Path
import hashlib,re
root=Path(__file__).resolve().parent.parent
shell=(root/'index.html').read_text();shell=shell[shell.index('<header class="wiki-header">'):shell.index('<main class="pokedex-main')]
shell=re.sub(r' aria-current="(?:page|location)"','',shell)
shell=shell.replace('<a href="machines/">','<a href="machines/" aria-current="page">')
def asset(path):return path+'?v='+hashlib.sha256((root/path).read_bytes()).hexdigest()[:12]
styles=''.join('<link rel="stylesheet" href="'+asset(path)+'">' for path in ['pokemon.css','pokemons/list.css','machines/list.css'])
parts=['<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><base href="../"><meta name="viewport" content="width=device-width,initial-scale=1"><title>招式学习机 · 青苔 Wiki</title><meta name="description" content="口袋妖怪青苔的 50 个 TM 与 8 个 HM，查看招式数值、可学习宝可梦以及地图获取地点。">'+styles+'<script src="'+asset('machines/list.js')+'" defer></script></head><body class="pokedex-page machines-page">'+shell+'<main class="pokedex-main"><h1>招式学习机</h1><nav class="breadcrumbs" aria-label="当前位置"><a href="./">百科首页</a><span>/</span><span aria-current="page">招式学习机</span></nav><p class="page-intro">查看本作 TM 与 HM 对应的招式、可学习宝可梦和获取地点。点击可学习条目展开名单，点击招式名称查看招式资料。</p><nav class="machine-toc" aria-label="学习机分类"><a href="machines/#tm">TM 招式学习机 · 50</a><a href="machines/#hm">HM 秘传学习机 · 8</a></nav><section class="filter-panel" aria-label="筛选招式学习机"><div class="catalog-count"><strong id="machine-total">—</strong><span>个学习机 · 50 TM / 8 HM</span></div><div class="filter-fields"><label class="name-filter" for="machine-search">查找学习机<input id="machine-search" type="search" placeholder="编号、招式或宝可梦" autocomplete="off"></label><label for="machine-kind">种类<select id="machine-kind"><option value="">全部学习机</option><option value="TM">TM</option><option value="HM">HM</option></select></label><label for="machine-type">属性<select id="machine-type"><option value="">全部属性</option></select></label><label for="machine-category">分类<select id="machine-category"><option value="">全部分类</option><option>物理</option><option>特殊</option><option>变化</option></select></label><button type="button" id="reset-machines">重置筛选</button></div></section><p id="machines-status" class="list-status" role="status">正在加载招式学习机…</p><p id="machines-empty" class="empty-state" hidden>没有找到对应学习机，试试其他名称或筛选条件。</p>']
for kind,title in [('tm','TM 招式学习机'),('hm','HM 秘传学习机')]:
 parts.append('<section id="'+kind+'-section" class="machine-section" aria-labelledby="'+kind+'"><h2 id="'+kind+'">'+title+'<small><span id="'+kind+'-count">—</span> 个</small></h2><div class="machines-table-wrap" role="region" aria-label="'+title+'表格，可横向滚动" tabindex="0"><table class="machines-table"><thead><tr>')
 for key,label in [('number','编号'),('name','招式'),('type','属性'),('category','分类'),('power','威力'),('accuracy','命中'),('pp','PP'),('learners','可学习条目')]:
  parts.append('<th scope="col" data-sort="'+key+'" aria-sort="none"><button type="button">'+label+'<span class="machine-sort" aria-hidden="true">↕</span></button></th>')
 parts.append('<th scope="col">获取地点</th></tr></thead><tbody id="'+kind+'-rows"></tbody></table></div></section>')
parts.append('<footer class="list-footer"><p>学习机编号、对应招式与可学习名单取自本作 ROM。不同形态按各自的可学习记录列出。</p><p>获取地点按地图事件整理，NPC 赠送和事件奖励可能需要先推进对应剧情。点击地点名称可查看地图；部分同名室内区域使用分区编号区分。</p></footer></main></body></html>')
(root/'machines/index.html').write_text('\n'.join(parts))
print('Built machine catalog page')
