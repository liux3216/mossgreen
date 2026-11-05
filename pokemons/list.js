'use strict';
const search = document.getElementById('pokemon-search');
const typeFilter = document.getElementById('pokemon-type');
const results = document.getElementById('pokemon-grid');
const status = document.getElementById('list-status');
const empty = document.getElementById('list-empty');
function element(tag, text) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  return node;
}
function verified(record) {
  return Object.values(record.stats).every(value => value > 0);
}
function createRow(record) {
  const row = element('tr');
  row.className = 'pokemon-row';
  row.dataset.pokemonId = record.id;
  const imageCell = element('td');
  const imageLink = element('a');
  imageLink.href = 'pokemons/' + record.id + '/';
  imageLink.tabIndex = -1;
  imageLink.setAttribute('aria-hidden', 'true');
  const image = element('img');
  image.src = 'data:image/png;base64,' + record.icon;
  image.width = 32;
  image.height = 32;
  image.alt = '';
  image.loading = 'lazy';
  image.decoding = 'async';
  imageLink.append(image);
  imageCell.append(imageLink);
  const number = element('td', record.gameDexId ? '#' + String(record.gameDexId).padStart(4, '0') : '—');
  const nameCell = element('td');
  const name = element('a', record.name);
  name.href = imageLink.href;
  name.className = 'pokemon-name';
  nameCell.append(name);
  if (record.otherForms.length) {
    const forms = element('details');
    forms.className = 'catalog-forms';
    forms.append(element('summary', '其他 ' + record.otherForms.length + ' 个形态'));
    record.otherForms.forEach((form, index) => {
      const label = form.name === record.name ? form.name + ' · 形态 ' + (index + 2) : form.name;
      const link = element('a', label);
      link.href = 'pokemons/' + form.id + '/';
      forms.append(link);
    });
    nameCell.append(forms);
  }
  const typeCell = element('td');
  const badges = element('div');
  badges.className = 'type-badges';
  if (verified(record)) {
    for (const type of record.types) {
      const badge = element('span', type);
      badge.className = 'pokedex-type';
      badge.dataset.type = type;
      badges.append(badge);
    }
  } else badges.append(element('small', '待核实'));
  typeCell.append(badges);
  const total = verified(record) ? Object.values(record.stats).reduce((sum, value) => sum + value, 0) : '—';
  const locations = element('td');
  locations.className = 'location-preview';
  const uniqueLocations = [...new Map(record.locations.map(place =>
    [place.anchor + ':' + place.method, place]
  )).values()];
  for (const place of uniqueLocations.slice(0, 2)) {
    const link = element('a', place.name + '（' + place.method + '）');
    link.href = 'locations/' + place.anchor.replace(/^location-/, '') + '/';
    locations.append(link);
  }
  if (!uniqueLocations.length) locations.append(element('span', '暂无野外遇敌记录'));
  if (uniqueLocations.length > 2) {
    const more = element('a', '全部 ' + uniqueLocations.length + ' 项');
    more.className = 'more-locations';
    more.href = 'pokemons/' + record.id + '/#encounters-heading';
    locations.append(more);
  }
  row.append(imageCell, number, nameCell, typeCell, element('td', String(total)), locations);
  return row;
}
function show(pokemon) {
  const query = search.value.trim().toLocaleLowerCase();
  const numberQuery = query.replace(/^#/, '');
  const visible = pokemon.filter(record =>
    ([record, ...record.otherForms].some(form => form.name.toLocaleLowerCase().includes(query)) ||
      (record.gameDexId && String(record.gameDexId).padStart(4, '0').includes(numberQuery))) &&
    (!typeFilter.value || [record, ...record.otherForms].some(form => verified(form) && form.types.includes(typeFilter.value)))
  );
  const wrap = element('div');
  wrap.className = 'pokedex-table-wrap';
  wrap.tabIndex = 0;
  wrap.setAttribute('role', 'region');
  wrap.setAttribute('aria-label', '宝可梦表格，按游戏图鉴编号排序，可横向滚动');
  const table = element('table');
  table.className = 'pokedex-table';
  const head = element('thead');
  const headRow = element('tr');
  for (const label of ['图像', '全国编号', '宝可梦', '属性', '种族值总和', '地图获取地点']) {
    const cell = element('th', label);
    cell.scope = 'col';
    headRow.append(cell);
  }
  head.append(headRow);
  const body = element('tbody');
  for (const record of visible) body.append(createRow(record));
  table.append(head, body);
  wrap.append(table);
  results.replaceChildren(wrap);
  results.hidden = visible.length === 0;
  empty.hidden = visible.length !== 0;
  status.textContent = '显示 ' + visible.length + ' / ' + pokemon.length + ' 个精灵条目 · 不同形态收在对应条目下';
}
async function load() {
  try {
    const response = await fetch('data/pokemon.json');
    if (!response.ok) throw new Error('宝可梦图鉴加载失败，请刷新重试。');
    const data = await response.json();
    const pokemon = Object.values(data)
      .filter(record => !record.catalogHidden && record.id === record.canonicalId && record.id === record.catalogPrimaryId)
      .map(record => ({ ...record, otherForms: record.formIds.filter(id => id !== record.id).map(id => data[id]) }))
      .sort((a, b) => (a.gameDexId || Infinity) - (b.gameDexId || Infinity) || a.id - b.id);
    document.getElementById('entry-total').textContent = pokemon.length;
    const types = [...new Set(pokemon.filter(verified).flatMap(record => record.types))];
    for (const type of types) {
      const option = element('option', type);
      option.value = type;
      typeFilter.append(option);
    }
    search.addEventListener('input', () => show(pokemon));
    typeFilter.addEventListener('change', () => show(pokemon));
    document.getElementById('reset-filters').addEventListener('click', () => {
      search.value = '';
      typeFilter.value = '';
      show(pokemon);
    });
    show(pokemon);
  } catch (error) {
    status.textContent = error.message;
  }
}
load();
