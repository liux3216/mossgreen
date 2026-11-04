'use strict';
const el = id => document.getElementById(id);
const statLabels = [
  ['hp', 'HP'], ['attack', '攻击'], ['defense', '防御'],
  ['specialAttack', '特攻'], ['specialDefense', '特防'], ['speed', '速度']
];
function node(tag, text) {
  const element = document.createElement(tag);
  if (text !== undefined) element.textContent = text;
  return element;
}
function showLocations(locations, method = '') {
  const fragment = document.createDocumentFragment();
  const visible = locations.filter(place => !method || place.method === method);
  for (const place of visible) {
    const row = node('tr');
    const location = node('td');
    const link = node('a', place.name);
    link.href = './#' + place.anchor;
    location.append(link, node('small', '地图 ' + place.mapId));
    const levels = place.levels.map(([low, high]) =>
      low === high ? 'Lv.' + low : 'Lv.' + low + '–' + high
    ).join('、');
    row.append(location, node('td', place.method), node('td', levels), node('td', place.chance + '%'));
    fragment.append(row);
  }
  el('locations').replaceChildren(fragment);
  const maps = new Set(visible.map(place => place.mapId)).size;
  el('location-count').textContent = maps + ' 个地图分区 · ' + visible.length + ' 组遇敌记录';
}
function render(pokemon) {
  document.title = pokemon.name + ' · 青苔 Wiki';
  el('name').textContent = pokemon.name;
  el('sprite').src = 'data:image/png;base64,' + pokemon.sprite;
  el('sprite').alt = pokemon.name + '的游戏立绘';
  el('identity-note').textContent = '本作内部编号 ' + pokemon.id;
  const verified = Object.values(pokemon.stats).every(value => value > 0);
  el('types').replaceChildren();
  if (verified) {
    for (const type of pokemon.types) {
      const badge = node('span', type);
      badge.className = 'type';
      badge.dataset.type = type;
      el('types').append(badge);
    }
  }
  el('stats').replaceChildren();
  if (verified) {
    for (const [key, label] of statLabels) {
      const value = pokemon.stats[key];
      const row = node('div');
      row.className = 'stat';
      const number = node('span', String(value));
      number.className = 'stat-value';
      const track = node('div');
      track.className = 'track';
      track.setAttribute('aria-hidden', 'true');
      const bar = node('div');
      bar.className = 'fill';
      bar.style.width = (value / 255 * 100) + '%';
      track.append(bar);
      row.append(node('span', label), number, track);
      el('stats').append(row);
    }
    el('total').textContent = Object.values(pokemon.stats).reduce((sum, value) => sum + value, 0);
  } else {
    el('stats').append(node('p', '这个形态的 ROM 基础数据表为空，种族值和基本资料待核实。'));
    el('total').textContent = '—';
  }
  el('type-text').textContent = verified ? pokemon.types.join(' / ') : '待核实';
  el('abilities').textContent = verified ? pokemon.abilities.map(ability => ability.name).join(' / ') || '待核实' : '待核实';
  el('catch-rate').textContent = verified ? pokemon.catchRate + ' / 255' : '待核实';
  for (const method of new Set(pokemon.locations.map(place => place.method))) {
    const option = node('option', method);
    option.value = method;
    el('method').append(option);
  }
  el('method').addEventListener('change', event => showLocations(pokemon.locations, event.target.value));
  showLocations(pokemon.locations);
  el('status').hidden = true;
  el('detail').hidden = false;
}
async function load() {
  try {
    const legacyId = new URLSearchParams(location.search).get('id');
    const id = document.body.dataset.pokemonId || legacyId;
    if (!document.body.dataset.pokemonId && legacyId && /^[1-9]\d*$/.test(legacyId)) {
      location.replace('pokemons/' + legacyId + '/');
      return;
    }
    if (!id || !/^[1-9]\d*$/.test(id)) throw new Error('请从宝可梦列表或遇敌图鉴点击名字进入资料页。');
    const response = await fetch('data/pokemon.json');
    if (!response.ok) throw new Error('资料暂时加载失败，请刷新重试。');
    const data = await response.json();
    if (!Object.hasOwn(data, id)) throw new Error('目前的资料页覆盖野外遇敌图鉴中出现的宝可梦，这个编号尚未收录。');
    render(data[id]);
  } catch (error) {
    el('status').hidden = true;
    el('error').hidden = false;
    el('error-message').textContent = error.message;
  }
}
load();
