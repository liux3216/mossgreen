'use strict';
const search = document.getElementById('pokemon-search');
const grid = document.getElementById('pokemon-grid');
const status = document.getElementById('list-status');
const empty = document.getElementById('list-empty');
function element(tag, text) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  return node;
}
function show(pokemon) {
  const query = search.value.trim().toLocaleLowerCase();
  const visible = pokemon.filter(record =>
    record.name.toLocaleLowerCase().includes(query) || String(record.id).includes(query)
  );
  const fragment = document.createDocumentFragment();
  for (const record of visible) {
    const link = element('a');
    link.className = 'pokemon-card';
    link.href = 'pokemons/' + record.id + '/';
    const image = element('img');
    image.src = 'data:image/png;base64,' + record.sprite;
    image.width = 80;
    image.height = 80;
    image.alt = '';
    image.loading = 'lazy';
    image.decoding = 'async';
    const info = element('div');
    info.append(element('small', '本作编号 ' + record.id), element('strong', record.name));
    const types = Object.values(record.stats).every(value => value > 0) ? record.types.join(' / ') : '资料待核实';
    info.append(element('span', types));
    link.append(image, info);
    fragment.append(link);
  }
  grid.replaceChildren(fragment);
  empty.hidden = visible.length !== 0;
  status.textContent = '显示 ' + visible.length + ' / ' + pokemon.length + ' 个宝可梦条目';
}
async function load() {
  try {
    const response = await fetch('data/pokemon.json');
    if (!response.ok) throw new Error('宝可梦列表加载失败，请刷新重试。');
    const records = Object.values(await response.json()).sort((a, b) => a.id - b.id);
    show(records);
    search.addEventListener('input', () => show(records));
  } catch (error) {
    status.textContent = error.message;
  }
}
load();
