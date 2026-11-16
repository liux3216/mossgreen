'use strict';

const byId = id => document.getElementById(id);
const rows = byId('item-rows');
const status = byId('items-status');
const table = byId('items-table');
const itemId = Number(document.body.dataset.itemId);
const collator = new Intl.Collator('zh-Hans', { numeric: true });
const numberFormat = new Intl.NumberFormat('zh-CN');
const methodOrder = new Map([
  ['地面拾取', 0],
  ['隐藏道具', 1],
  ['NPC赠送／事件奖励', 2],
  ['商店购买', 3],
  ['野生宝可梦携带', 4],
]);

function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}

function link(text, path) {
  const node = element('a', text);
  node.href = path;
  return node;
}

function orderedSources(sources) {
  return [...sources].sort((a, b) =>
    methodOrder.get(a.method) - methodOrder.get(b.method) || collator.compare(a.name, b.name));
}

function sourcePreview(source) {
  const line = element('div', undefined, 'item-place');
  line.append(link(source.name, source.path), element('small', source.method));
  return line;
}

function catalogRow(item, sources) {
  const path = 'items/' + item.id + '/';
  const row = element('tr');
  row.id = 'item-' + item.id;

  const nameCell = element('td');
  const identity = link(item.name, path);
  identity.className = 'item-identity';
  const icon = element('img');
  icon.src = 'data:image/png;base64,' + item.icon;
  icon.alt = '';
  icon.width = icon.height = 24;
  icon.loading = 'lazy';
  identity.prepend(icon);
  nameCell.append(identity);

  const locations = element('td', undefined, 'item-locations');
  for (const source of sources.slice(0, 2)) locations.append(sourcePreview(source));
  if (sources.length > 2) {
    const more = link('全部 ' + sources.length + ' 项', path + '#item-sources');
    more.className = 'item-all-sources';
    locations.append(more);
  }
  if (!sources.length) locations.textContent = '暂未确认获取地点';

  row.append(
    element('td', item.id), nameCell,
    element('td', item.pocket),
    element('td', item.price === null ? '—' : numberFormat.format(item.price), 'item-price'),
    locations,
  );
  return row;
}

function includesLocation(source, query) {
  return wikiLanguage.matches(source.name, query) || source.mapId.includes(query)
    || source.holders?.some(holder => wikiLanguage.matches(holder.name, query));
}

function loadCatalog(items) {
  const search = byId('item-search');
  const pocket = byId('item-pocket');
  const method = byId('item-method');
  const headers = [...table.querySelectorAll('th[data-sort]')];
  let sortKey = 'id';
  let direction = 1;

  function draw() {
    const query = search.value.trim().normalize('NFKC').toLowerCase();
    const id = /^#?\d+$/.test(query) ? Number(query.replace('#', '')) : null;
    const filtered = [];

    for (const item of items) {
      if (pocket.value && item.pocket !== pocket.value) continue;
      let sources = method.value ? item.locations.filter(source => source.method === method.value) : item.locations;
      if (method.value && !sources.length) continue;

      if (id !== null) {
        if (item.id !== id) continue;
      } else if (query && !wikiLanguage.matches(item.name, query)
          && !item.alias?.toLowerCase().includes(query)) {
        sources = sources.filter(source => includesLocation(source, query));
        if (!sources.length) continue;
      }
      filtered.push({ item, sources });
    }

    filtered.sort(({ item: a }, { item: b }) => {
      const left = a[sortKey], right = b[sortKey];
      if (left === null || right === null)
        return Number(left === null) - Number(right === null) || a.id - b.id;
      const comparison = typeof left === 'number' ? left - right : document.documentElement.lang === 'en' ? wikiLanguage.compare(left, right) : collator.compare(left, right);
      return comparison * direction || a.id - b.id;
    });

    rows.replaceChildren(...filtered.map(({item, sources}) => catalogRow(item, orderedSources(sources))));
    table.hidden = !filtered.length;
    byId('items-empty').hidden = Boolean(filtered.length);
    status.textContent = '显示 ' + filtered.length + ' / ' + items.length + ' 件道具';
  }

  search.addEventListener('input', draw);
  pocket.addEventListener('change', draw);
  method.addEventListener('change', draw);
  byId('item-reset').addEventListener('click', () => {
    search.value = pocket.value = method.value = '';
    draw();
    search.focus();
  });
  for (const header of headers) {
    header.querySelector('button').addEventListener('click', () => {
      const key = header.dataset.sort;
      direction = sortKey === key ? -direction : 1;
      sortKey = key;
      for (const th of headers) th.removeAttribute('aria-sort');
      header.setAttribute('aria-sort', direction === 1 ? 'ascending' : 'descending');
      draw();
    });
  }
  draw();
  if (location.hash.startsWith('#item-')) document.getElementById(location.hash.slice(1))?.scrollIntoView();
}

function showItem(item) {
  if (!item) {
    status.textContent = '找不到这件道具。';
    return;
  }
  for (const source of orderedSources(item.locations)) {
    const row = element('tr');
    const place = element('td');
    place.append(link(source.name, source.path));
    const holders = element('td');
    for (const mon of source.holders || []) {
      const holder = element('span', undefined, 'item-holder');
      holder.append(link(mon.name, 'pokemons/' + mon.id + '/'), element('small', ' ' + mon.chance + '%'));
      holders.append(holder);
    }
    if (!source.holders?.length) holders.textContent = '—';
    row.append(place, element('td', source.method), holders);
    rows.append(row);
  }
  table.hidden = !item.locations.length;
  status.textContent = item.locations.length ? '共 ' + item.locations.length + ' 项获取记录' : '暂未确认获取地点。';
  if (item.locations.some(source => source.holders?.length)) {
    table.after(element('p', '携带比例以遇到该宝可梦为前提。', 'item-source-note'));
  }
  if (location.hash === '#item-sources') byId('item-sources').scrollIntoView();
}

async function load() {
  try {
    const response = await fetch(document.body.dataset.itemsUrl);
    if (!response.ok) throw new Error('Item data: HTTP ' + response.status);
    const items = await response.json();
    if (itemId) showItem(items.find(item => item.id === itemId));
    else loadCatalog(items);
  } catch (error) {
    console.error(error);
    status.textContent = '道具资料加载失败，请刷新页面重试。';
  }
}

load();
