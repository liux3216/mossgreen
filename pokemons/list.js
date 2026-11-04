'use strict';
const search = document.getElementById('pokemon-search');
const typeFilter = document.getElementById('pokemon-type');
const results = document.getElementById('pokemon-grid');
const status = document.getElementById('list-status');
const empty = document.getElementById('list-empty');
const generations = [
  { id: 1, name: '第一世代', range: '#0001—#0151' },
  { id: 2, name: '第二世代', range: '#0152—#0251' },
  { id: 3, name: '第三世代', range: '#0252—#0386' },
  { id: 4, name: '第四世代', range: '#0387—#0493' },
  { id: 5, name: '第五世代', range: '#0494—#0649' },
  { id: 6, name: '第六世代', range: '#0650—#0721' },
  { id: 7, name: '第七世代', range: '#0722—#0809' },
  { id: 8, name: '第八世代', range: '#0810—#0905' },
  { id: 9, name: '第九世代', range: '#0906—#1025' },
  { id: 0, name: '其他编号', range: '本作特殊形态' }
];
let selectedGeneration = null;
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
  const number = element('td', record.nationalId ? '#' + String(record.nationalId).padStart(4, '0') : '—');
  const nameCell = element('td');
  const name = element('a', record.name);
  name.href = imageLink.href;
  name.className = 'pokemon-name';
  nameCell.append(name, element('small', '本作编号 ' + record.id));
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
    link.href = './#' + place.anchor;
    locations.append(link);
  }
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
    (record.name.toLocaleLowerCase().includes(query) ||
      String(record.id).includes(numberQuery) ||
      (record.nationalId && String(record.nationalId).padStart(4, '0').includes(numberQuery))) &&
    (!typeFilter.value || (verified(record) && record.types.includes(typeFilter.value))) &&
    (selectedGeneration === null || record.generation === selectedGeneration)
  );
  const fragment = document.createDocumentFragment();
  for (const generation of generations) {
    const entries = visible.filter(record => record.generation === generation.id);
    if (!entries.length) continue;
    const section = element('section');
    section.className = 'generation-section';
    const heading = element('h2', generation.name);
    heading.id = 'generation-' + generation.id;
    heading.append(element('small', generation.range));
    section.setAttribute('aria-labelledby', heading.id);
    const wrap = element('div');
    wrap.className = 'pokedex-table-wrap';
    wrap.tabIndex = 0;
    wrap.setAttribute('role', 'region');
    wrap.setAttribute('aria-label', generation.name + '宝可梦表格，可横向滚动');
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
    for (const record of entries) body.append(createRow(record));
    table.append(head, body);
    wrap.append(table);
    section.append(heading, wrap);
    fragment.append(section);
  }
  results.replaceChildren(fragment);
  empty.hidden = visible.length !== 0;
  status.textContent = '显示 ' + visible.length + ' / ' + pokemon.length + ' 个条目 · 像素图标按原尺寸显示';
}
async function load() {
  try {
    const response = await fetch('data/pokemon.json');
    if (!response.ok) throw new Error('宝可梦图鉴加载失败，请刷新重试。');
    const pokemon = Object.values(await response.json()).sort((a, b) =>
      (a.nationalId || Infinity) - (b.nationalId || Infinity) || a.id - b.id
    );
    document.getElementById('entry-total').textContent = pokemon.length;
    const types = [...new Set(pokemon.filter(verified).flatMap(record => record.types))];
    for (const type of types) {
      const option = element('option', type);
      option.value = type;
      typeFilter.append(option);
    }
    const controls = document.getElementById('generation-filters');
    for (const group of [{ id: null, name: '全部' }, ...generations]) {
      const button = element('button', group.name);
      button.type = 'button';
      button.setAttribute('aria-pressed', String(group.id === selectedGeneration));
      button.addEventListener('click', () => {
        selectedGeneration = group.id;
        for (const other of controls.children) other.setAttribute('aria-pressed', String(other === button));
        show(pokemon);
      });
      controls.append(button);
    }
    search.addEventListener('input', () => show(pokemon));
    typeFilter.addEventListener('change', () => show(pokemon));
    document.getElementById('reset-filters').addEventListener('click', () => {
      search.value = '';
      typeFilter.value = '';
      selectedGeneration = null;
      for (const button of controls.children) button.setAttribute('aria-pressed', String(button === controls.firstElementChild));
      show(pokemon);
    });
    show(pokemon);
  } catch (error) {
    status.textContent = error.message;
  }
}
load();
