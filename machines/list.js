'use strict';
const el = id => document.getElementById(id);
const search = el('machine-search'), kind = el('machine-kind'), type = el('machine-type'), category = el('machine-category');
let machines = [], pokemon = {}, sortKey = 'number', direction = 1;
const opened = new Set();
function node(tag, text) { const n = document.createElement(tag); if (text !== undefined) n.textContent = text; return n; }
function pokemonLabel(p) {
  const forms = p.formIds || [p.id];
  const primary = pokemon[p.catalogPrimaryId];
  return forms.length > 1 && primary?.name === p.name ? p.name + ' · 形态 ' + (forms.indexOf(p.id) + 1) : p.name;
}
function fillLearners(cell, machine) {
  if (cell.childElementCount) return;
  cell.append(node('h3', machine.id + '「' + machine.name + '」· 可学习宝可梦'));
  const grid = node('div'); grid.className = 'machine-learners';
  for (const id of machine.learners) {
    const p = pokemon[id]; if (!p) continue;
    const a = node('a'); a.href = 'pokemons/' + id + '/';
    const image = node('img'); image.src = 'data:image/png;base64,' + p.icon;
    image.width = 32; image.height = 32; image.alt = ''; image.loading = 'lazy';
    const text = node('span'); text.append(node('strong', pokemonLabel(p)), node('small', p.gameDexId ? '#' + p.gameDexId : '—'));
    a.append(image, text); grid.append(a);
  }
  if (!machine.learners.length) cell.append(node('p', '暂无可学习记录。'));
  else cell.append(grid);
}
function locationLine(place) {
  const line = node('div'); line.className = 'machine-place';
  const a = node('a', place.name); a.href = place.path;
  line.append(a, node('small', place.method)); return line;
}
function rows(machine) {
  const row = node('tr'); row.id = machine.id; row.className = 'machine-row'; row.dataset.machine = machine.id;
  const code = node('td'), permalink = node('a', machine.id); permalink.href = 'machines/#' + machine.id; code.append(permalink);
  const nameCell = node('td'), link = node('a', machine.name); link.href = 'moves/#move-' + machine.moveId; link.className = 'machine-move'; nameCell.append(link);
  const typeCell = node('td'), badge = node('span', machine.type); badge.className = 'pokedex-type'; badge.dataset.type = machine.type; typeCell.append(badge);
  const categoryCell = node('td'), label = node('span', machine.category); label.className = 'move-category'; label.dataset.category = machine.category; categoryCell.append(label);
  const learnerCell = node('td'), button = node('button', machine.learners.length + ' 个条目'); button.type = 'button'; button.className = 'machine-count';
  const detail = node('tr'); detail.className = 'machine-details'; detail.id = 'learners-' + machine.id; detail.hidden = !opened.has(machine.id);
  const cell = node('td'); cell.colSpan = 9; detail.append(cell);
  button.setAttribute('aria-controls', detail.id); button.setAttribute('aria-expanded', String(!detail.hidden));
  button.setAttribute('aria-label', machine.id + '「' + machine.name + '」可学习条目：' + machine.learners.length);
  if (!detail.hidden) fillLearners(cell, machine);
  button.onclick = () => {
    const show = detail.hidden; detail.hidden = !show; button.setAttribute('aria-expanded', String(show));
    if (show) { opened.add(machine.id); fillLearners(cell, machine); history.replaceState(null, '', 'machines/#' + machine.id); }
    else opened.delete(machine.id);
  };
  learnerCell.append(button);
  const locations = node('td'); locations.className = 'machine-locations';
  const priority = { '地面拾取': 0, '隐藏道具': 1, 'NPC赠送／事件奖励': 2, '商店购买': 3 };
  const places = [...machine.locations].sort((a, b) => (priority[a.method] ?? 4) - (priority[b.method] ?? 4) || a.name.localeCompare(b.name, 'zh-Hans'));
  places.slice(0, 2).forEach(place => locations.append(locationLine(place)));
  if (places.length > 2) {
    const more = node('details'); more.className = 'more-machine-places'; more.append(node('summary', '另 ' + (places.length - 2) + ' 处'));
    places.slice(2).forEach(place => more.append(locationLine(place))); locations.append(more);
  }
  if (!places.length) locations.append(node('span', '暂未确认获取地点'));
  row.append(code, nameCell, typeCell, categoryCell, node('td', machine.power || '—'), node('td', machine.accuracy || '—'), node('td', machine.pp), learnerCell, locations);
  return [row, detail];
}
function draw() {
  const query = search.value.trim().toLowerCase(), number = /^#?\d+$/.test(query) ? Number(query.replace('#', '')) : null;
  const filtered = machines.filter(m => (!kind.value || m.kind === kind.value) && (!type.value || m.type === type.value) && (!category.value || m.category === category.value) &&
    (!query || (number !== null ? m.number === number : m.id.toLowerCase().includes(query.replace(/\s+/g, '')) || m.name.toLowerCase().includes(query) || m.learners.some(id => pokemon[id]?.name.toLowerCase().includes(query)))));
  filtered.sort((a, b) => {
    const av = sortKey === 'learners' ? a.learners.length : a[sortKey], bv = sortKey === 'learners' ? b.learners.length : b[sortKey];
    return (typeof av === 'number' ? av - bv : String(av).localeCompare(String(bv), 'zh-Hans')) * direction || a.number - b.number;
  });
  for (const value of ['TM', 'HM']) {
    const entries = filtered.filter(m => m.kind === value), body = el(value.toLowerCase() + '-rows'), fragment = document.createDocumentFragment();
    for (const machine of entries) fragment.append(...rows(machine)); body.replaceChildren(fragment);
    el(value.toLowerCase() + '-section').hidden = !entries.length; el(value.toLowerCase() + '-count').textContent = entries.length;
  }
  el('machines-status').textContent = '显示 ' + filtered.length + ' / ' + machines.length + ' 个学习机';
  el('machines-empty').hidden = !!filtered.length;
  for (const th of document.querySelectorAll('th[data-sort]')) {
    th.setAttribute('aria-sort', th.dataset.sort === sortKey ? (direction === 1 ? 'ascending' : 'descending') : 'none');
    th.querySelector('.machine-sort').textContent = th.dataset.sort === sortKey ? (direction === 1 ? '↑' : '↓') : '↕';
  }
}
function reset() { search.value = ''; kind.value = ''; type.value = ''; category.value = ''; draw(); }
function followHash() {
  const id = decodeURIComponent(location.hash.slice(1)).toUpperCase(); if (!/^(TM|HM)\d{2}$/.test(id) || !machines.some(m => m.id === id)) return;
  search.value = id; kind.value = ''; type.value = ''; category.value = ''; opened.add(id); draw();
  requestAnimationFrame(() => el(id)?.scrollIntoView({ block: 'start' }));
}
async function load() {
  try {
    const responses = await Promise.all([fetch('data/machines.json'), fetch('data/pokemon.json')]);
    if (responses.some(r => !r.ok)) throw Error('招式学习机数据加载失败，请刷新重试。');
    [machines, pokemon] = await Promise.all(responses.map(r => r.json()));
    el('machine-total').textContent = machines.length;
    for (const value of [...new Set(machines.map(m => m.type))]) { const option = node('option', value); option.value = value; type.append(option); }
    draw(); followHash();
  } catch (error) { el('machines-status').textContent = error.message; }
}
for (const control of [search, kind, type, category]) control.addEventListener(control === search ? 'input' : 'change', draw);
el('reset-machines').onclick = () => { reset(); search.focus(); };
for (const th of document.querySelectorAll('th[data-sort]')) th.querySelector('button').onclick = () => {
  if (sortKey === th.dataset.sort) direction *= -1; else { sortKey = th.dataset.sort; direction = 1; } draw();
};
for (const link of document.querySelectorAll('.machine-toc a')) link.addEventListener('click', reset);
window.addEventListener('hashchange', followHash); load();
