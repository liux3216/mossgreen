# -*- coding: utf-8 -*-
"""Build the Chinese walkthrough from the credited, author-authorized guide notes."""
from pathlib import Path
import json,re,html,hashlib
root=Path(__file__).resolve().parent.parent
data=json.loads((root/'data/walkthrough.json').read_text())
places={}
for place in json.loads((root/'data/atlas.json').read_text()):places.setdefault(place['mapId'],place)
def esc(value):return html.escape(str(value),quote=True)
shell=(root/'index.html').read_text();shell=shell[shell.index('<header class="wiki-header">'):shell.index('<main class="pokedex-main')]
shell=re.sub(r' aria-current="(?:page|location)"','',shell)
shell=shell.replace('<a href="walkthrough/">','<a href="walkthrough/" aria-current="page">')
styles=[]
for asset in ['pokemon.css','pokemons/list.css','walkthrough/style.css']:
 digest=hashlib.sha256((root/asset).read_bytes()).hexdigest()[:12];styles.append('<link rel="stylesheet" href="'+asset+'?v='+digest+'">')
parts=['<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><base href="../"><meta name="viewport" content="width=device-width,initial-scale=1"><title>流程攻略 · 青苔 Wiki</title><meta name="description" content="口袋妖怪青苔中文流程攻略：第一大陆、第二大陆、八把钥匙、通关后剧情与支线任务。">'+''.join(styles)+'</head><body class="pokedex-page walkthrough-page">'+shell+'<main class="pokedex-main walkthrough-main"><h1>流程攻略</h1><nav class="breadcrumbs" aria-label="当前位置"><a href="./">百科首页</a><span>/</span><span aria-current="page">流程攻略</span></nav><p class="page-intro guide-intro">按剧情顺序整理主线、徽章与通关后任务。点击目录跳转章节，点击地点标签查看对应地图。</p><p class="guide-source">中文整理自 <a href="'+esc(data['source']['url'])+'" target="_blank" rel="noopener noreferrer">Almanaque Pokémon Verde Musgo</a>。地名优先对应本作汉化地图；未能确认的人名、译名或原文图片位置会在相关步骤注明。</p><nav id="contents" class="guide-toc" aria-labelledby="contents-heading"><h2 id="contents-heading">攻略目录</h2><ol>']
ids=set()
for section in data['sections']:
 assert section['id'] not in ids;ids.add(section['id'])
 parts.append('<li><a href="walkthrough/#'+esc(section['id'])+'">'+esc(section['title'])+'</a></li>')
parts.append('</ol></nav>')
for section in data['sections']:
 parts.append('<section id="'+esc(section['id'])+'" class="guide-chapter" aria-labelledby="heading-'+esc(section['id'])+'"><h2 id="heading-'+esc(section['id'])+'">'+esc(section['title'])+'</h2>')
 if section['intro']:parts.append('<p class="guide-chapter-intro">'+esc(section['intro'])+'</p>')
 for stage in section['stages']:
  assert stage['id'] not in ids;ids.add(stage['id'])
  parts.append('<section id="'+esc(stage['id'])+'" class="guide-stage" aria-labelledby="heading-'+esc(stage['id'])+'"><h3 id="heading-'+esc(stage['id'])+'"><a href="walkthrough/#'+esc(stage['id'])+'">'+esc(stage['title'])+'</a></h3><ol class="guide-steps">')
  parts.extend('<li>'+esc(step)+'</li>' for step in stage['steps']);parts.append('</ol>')
  if stage['tips']:parts.append('<aside class="guide-tips" aria-label="流程提示">'+''.join('<p>'+esc(tip)+'</p>' for tip in stage['tips'])+'</aside>')
  if stage['places']:
   parts.append('<nav class="guide-places" aria-label="'+esc(stage['title'])+'相关地图"><span>相关地图</span>')
   for map_id in dict.fromkeys(stage['places']):
    assert map_id in places,map_id;p=places[map_id]
    parts.append('<a href="'+esc(p['path'])+'">'+esc(p['name'])+'</a>')
   parts.append('</nav>')
  parts.append('</section>')
 parts.append('<p class="guide-back"><a href="walkthrough/#contents">返回攻略目录 ↑</a></p></section>')
source=data['source']
parts.append('<footer class="guide-credits"><p>原攻略作者：'+esc('、'.join(source['authors']))+'。'+esc(source['permission'])+'</p><p>来源：<a href="'+esc(source['url'])+'" target="_blank" rel="noopener noreferrer">'+esc(source['title'])+'</a>，流程部分（原文第 13–27 页）。本页为中文流程整理；原指南与汉化版本可能存在差异，剧情分支以游戏内对话为准。</p></footer></main></body></html>')
(root/'walkthrough/index.html').write_text('\n'.join(parts))
print('Built walkthrough:',len(data['sections']),'chapters,',sum(len(s['stages']) for s in data['sections']),'stages')
