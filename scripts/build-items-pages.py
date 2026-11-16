"""Generate the item list and detail routes with the wiki's shared layout."""
from hashlib import sha256
from html import escape
from pathlib import Path
from wiki_language import add_wiki_language
import json
import re

ROOT = Path(__file__).resolve().parent.parent
ITEMS = ROOT / 'items'
DATA = ROOT / 'data/items.json'


def asset(name):
    return name + '?v=' + sha256((ROOT / name).read_bytes()).hexdigest()[:12]


def shell(title, base, main, body_attributes=''):
    home = (ROOT / 'index.html').read_text()
    navigation = home[home.index('<header class="wiki-header">'):home.index('<main class="pokedex-main')]
    navigation = re.sub(r' aria-current="(?:page|location)"', '', navigation)
    navigation = navigation.replace('<a href="items/">', '<a href="items/" aria-current="page">')
    styles = ''.join(
        f'<link rel="stylesheet" href="{asset(path)}">'
        for path in ('pokemon.css', 'pokemons/list.css', 'items/list.css')
    )
    return f'''<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<base href="{base}">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(title)} · 青苔 Wiki</title>
{styles}
<script src="{asset('items/list.js')}" defer></script>
</head>
<body class="pokedex-page items-page" data-items-url="{asset('data/items.json')}"{body_attributes}>
{navigation}
<main class="pokedex-main">
{main}
</main>
</body>
</html>
'''


def breadcrumbs(current=None):
    catalog = '<a href="items/">道具一览</a><span>/</span>' if current else ''
    return (
        '<nav class="breadcrumbs" aria-label="当前位置">'
        '<a href="./">百科首页</a><span>/</span>'
        f'{catalog}<span aria-current="page">{escape(current or "道具一览")}</span></nav>'
    )


def label_list(values):
    return ''.join(f'<option>{escape(label)}</option>' for label in values)


def catalog_page(rows):
    pockets = list(dict.fromkeys(item['pocket'] for item in rows))
    methods = ('地面拾取', '隐藏道具', 'NPC赠送／事件奖励', '商店购买', '野生宝可梦携带')
    headings = (
        ('id', '编号'), ('name', '名称'), ('pocket', '口袋'), ('price', '价格'),
    )
    headers = ''.join(
        f'<th scope="col" data-sort="{key}"' + (' aria-sort="ascending"' if key == 'id' else '')
        + f'><button type="button">{label}</button></th>'
        for key, label in headings
    )
    return shell('道具一览', '../', f'''
<h1>道具一览</h1>
{breadcrumbs()}
<section class="filter-panel" aria-label="筛选道具">
  <div class="catalog-count"><strong>{len(rows)}</strong><span>件道具</span></div>
  <div class="filter-fields">
    <label class="name-filter">搜索<input id="item-search" type="search" placeholder="名称、编号、地点或宝可梦" autocomplete="off"></label>
    <label><span id="item-pocket-label">口袋</span><select id="item-pocket" aria-labelledby="item-pocket-label"><option value="">全部口袋</option>{label_list(pockets)}</select></label>
    <label><span id="item-method-label">获取方式</span><select id="item-method" aria-labelledby="item-method-label"><option value="">全部方式</option>{label_list(methods)}</select></label>
    <button type="button" id="item-reset">重置筛选</button>
  </div>
</section>
<p id="items-status" class="list-status" role="status">正在加载道具…</p>
<p id="items-empty" class="empty-state" hidden>没有找到符合条件的道具。</p>
<div class="items-table-wrap" id="items-table" role="region" aria-label="道具一览表" tabindex="0" hidden>
  <table class="items-table">
    <thead><tr>{headers}<th scope="col">获取地点</th></tr></thead>
    <tbody id="item-rows"></tbody>
  </table>
</div>
<p class="list-footer">价格取自本作 ROM。部分获取方式有剧情条件，获取地点会随资料核对补充。</p>
''')


def detail_page(item):
    machine = (
        f' <a href="machines/#{item["machine"]}">查看可学习的宝可梦</a>' if 'machine' in item else ''
    )
    return shell(item['name'], '../../', f'''
<h1>{escape(item["name"])}</h1>
{breadcrumbs(item["name"])}
<div class="item-summary">
  <img src="data:image/png;base64,{item["icon"]}" alt="" width="48" height="48">
  <dl>
    <div><dt>编号</dt><dd>{item["id"]}</dd></div>
    <div><dt>口袋</dt><dd>{escape(item["pocket"])}</dd></div>
    <div><dt>价格</dt><dd>{f'{item["price"]:,}' if item["price"] else '—'}</dd></div>
  </dl>
</div>
<p class="page-intro">{escape(item["description"])}{machine}</p>
<section aria-labelledby="item-sources">
  <h2 id="item-sources">获取地点</h2>
  <p id="items-status" class="list-status" role="status">正在加载获取地点…</p>
  <div class="items-table-wrap" id="items-table" role="region" aria-label="获取地点表" tabindex="0" hidden>
    <table class="items-table item-source-table">
      <thead><tr><th scope="col">地点</th><th scope="col">获取方式</th><th scope="col">携带宝可梦</th></tr></thead>
      <tbody id="item-rows"></tbody>
    </table>
  </div>
</section>
''', f' data-item-id="{item["id"]}"')


def main():
    rows = json.loads(DATA.read_text())
    (ITEMS / 'index.html').write_text(add_wiki_language(catalog_page(rows)))
    for item in rows:
        folder = ITEMS / str(item['id'])
        folder.mkdir(parents=True, exist_ok=True)
        (folder / 'index.html').write_text(add_wiki_language(detail_page(item)))
    print(f'Built the item catalog and {len(rows)} detail routes')


if __name__ == '__main__':
    main()
