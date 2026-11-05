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
    link.href = 'locations/' + place.anchor.replace(/^location-/, '') + '/';
    location.append(link, node('small', '地图 ' + place.mapId));
    const levels = place.levels.map(([low, high]) =>
      low === high ? 'Lv.' + low : 'Lv.' + low + '–' + high
    ).join('、');
    row.append(location, node('td', place.method), node('td', levels), node('td', place.chance + '%'));
    fragment.append(row);
  }
  if (!visible.length) {
    const row = node('tr');
    const cell = node('td', '暂无野外随机遇敌记录，其他获取方式待补充。');
    cell.colSpan = 4;
    row.append(cell);
    fragment.append(row);
  }
  el('locations').replaceChildren(fragment);
  const maps = new Set(visible.map(place => place.mapId)).size;
  el('location-count').textContent = maps + ' 个地图分区 · ' + visible.length + ' 组遇敌记录';
}
function evolutionCard(record, currentId) {
  const link = node('a');
  link.href = 'pokemons/' + record.id + '/';
  link.className = 'evolution-pokemon';
  if (record.id === currentId) link.setAttribute('aria-current', 'page');
  const image = node('img');
  image.src = 'data:image/png;base64,' + record.sprite;
  image.alt = ''; image.width = 64; image.height = 64;
  link.append(image, node('strong', record.name), node('small', record.gameDexId ? '#' + record.gameDexId : '—'));
  return link;
}
function showGrowth(pokemon, data, growth) {
  const host = el('evolution-chain'), learnset = el('learnset');
  host.replaceChildren(); learnset.replaceChildren();
  const info = growth?.species[pokemon.id];
  if (!info) {
    host.append(node('p', growth ? '此形态的进化资料待核实。' : '进化资料暂时加载失败，请刷新重试。'));
    el('learnset-note').textContent = growth ? '此形态的升级招式资料待核实。' : '升级招式暂时加载失败，请刷新重试。';
    return;
  }
  const family = new Set([pokemon.id]);
  let changed = true;
  while (changed) {
    changed = false;
    for (const edge of growth.evolutions) {
      if (family.has(edge.from) || family.has(edge.to)) {
        for (const id of [edge.from, edge.to]) {
          if (!family.has(id)) { family.add(id); changed = true; }
        }
      }
    }
  }
  const edges = growth.evolutions.filter(e => family.has(e.from) && family.has(e.to));
  if (!edges.length) host.append(node('p', info.invalidEvolution ? '此形态的进化记录异常，条件待核实。' : '没有进化记录。'));
  else {
    const roots = [...family].filter(id => !edges.some(e => e.to === id));
    const paths = [];
    function visit(id, path, visited) {
      const next = edges.filter(e => e.from === id && !visited.has(e.to));
      if (!next.length) { paths.push(path); return; }
      for (const edge of next) visit(edge.to, [...path, edge], new Set([...visited, edge.to]));
    }
    for (const id of roots.length ? roots : [pokemon.id]) visit(id, [], new Set([id]));
    for (const path of paths) {
      if (!path.length) continue;
      const row = node('div'); row.className = 'evolution-path';
      row.append(evolutionCard(data[path[0].from], pokemon.id));
      for (const edge of path) {
        const arrow = node('div'); arrow.className = 'evolution-condition';
        const symbol = node('span', '→'); symbol.setAttribute('aria-hidden', 'true');
        arrow.append(node('small', edge.condition), symbol);
        row.append(arrow, evolutionCard(data[edge.to], pokemon.id));
      }
      host.append(row);
    }
  }
  el('learnset-note').textContent = info.invalidLearnset ? '部分升级招式记录异常，以下仅列出可识别的记录。' : '按等级列出本形态的升级招式。';
  const rows = [...info.learnset].sort((a, b) => a.level - b.level);
  for (const entry of rows) {
    const move = growth.moves[entry.move];
    const row = node('tr');
    const type = node('td'), badge = node('span', move.type);
    badge.className = 'pokedex-type'; badge.dataset.type = move.type; type.append(badge);
    const category = node('td'), label = node('span', move.category);
    label.className = 'move-category'; label.dataset.category = move.category; category.append(label);
    const moveCell = node('td'), moveLink = node('a', move.name);
    moveLink.href = 'moves/#move-' + entry.move; moveCell.append(moveLink);
    row.append(node('td', String(entry.level)), moveCell, type, category,
      node('td', move.power ? String(move.power) : '—'), node('td', move.accuracy ? String(move.accuracy) : '—'), node('td', String(move.pp)));
    learnset.append(row);
  }
  if (!rows.length) {
    const row = node('tr'), cell = node('td', '暂无可识别的升级招式记录。');
    cell.colSpan = 7; row.append(cell); learnset.append(row);
  }
}
async function showIntroduction(pokemon) {
  try {
    const response = await fetch('data/introductions.json');
    if (!response.ok) throw new Error('Introduction unavailable');
    const data = await response.json();
    const mapping = data.pokemon[pokemon.id];
    const entry = mapping && data.species[mapping.speciesId];
    if (!entry) {
      el('dex-entry-text').textContent = '暂无可核实的图鉴介绍。';
      return;
    }
    el('dex-entry-text').textContent = entry.text;
    const source = node('a', entry.version);
    source.href = entry.source;
    source.target = '_blank';
    source.rel = 'noopener noreferrer';
    el('dex-entry-source').replaceChildren(document.createTextNode('来源：'), source);
    if (mapping.baseDescription) {
      el('dex-entry-source').prepend(document.createTextNode('此形态采用' + entry.name + '的本体介绍。 '));
    }
  } catch (_) {
    el('dex-entry-text').textContent = '图鉴介绍暂时加载失败，请刷新重试。';
  }
}
function render(pokemon, data, growth) {
  document.title = pokemon.name + ' · 青苔 Wiki';
  el('name').textContent = pokemon.name;
  el('breadcrumb-name').textContent = pokemon.name;
  el('sprite').src = 'data:image/png;base64,' + pokemon.sprite;
  el('sprite').alt = pokemon.name + '的游戏立绘';
  el('identity-note').textContent = pokemon.gameDexId ? '#' + pokemon.gameDexId : '未分配图鉴编号';
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
  const forms = (pokemon.formIds || [pokemon.id]).map(id => data[id]).filter(Boolean);
  const currentFormIndex = forms.findIndex(form => form.id === pokemon.id);
  if (forms.length > 1) {
    el('form-section').hidden = false;
    el('form-label').hidden = false;
    el('form-label').textContent = '形态 ' + (currentFormIndex + 1) + ' / ' + forms.length;
    const options = document.createDocumentFragment();
    forms.forEach((form, index) => {
      const link = node('a');
      link.className = 'form-option';
      link.href = 'pokemons/' + form.id + '/';
      if (form.id === pokemon.id) link.setAttribute('aria-current', 'page');
      const image = node('img');
      image.src = 'data:image/png;base64,' + form.sprite;
      image.alt = '';
      image.width = 56;
      image.height = 56;
      const description = node('span');
      description.append(node('strong', form.name + ' · 形态 ' + (index + 1)));
      const typeLabel = Object.values(form.stats).every(value => value > 0) ? form.types.join(' / ') : '资料待核实';
      description.append(node('small', typeLabel));
      link.append(image, description);
      options.append(link);
    });
    el('form-options').replaceChildren(options);
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
      bar.dataset.stat = key;
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
  el('abilities').replaceChildren();
  if (verified && pokemon.abilities.length) {
    pokemon.abilities.forEach((ability, index) => {
      if (index) el('abilities').append(document.createTextNode(' / '));
      const link = node('a', ability.name);
      link.href = 'abilities/#ability-' + ability.id;
      el('abilities').append(link);
    });
  } else el('abilities').textContent = '待核实';
  el('catch-rate').textContent = verified ? pokemon.catchRate + ' / 255' : '待核实';
  for (const method of new Set(pokemon.locations.map(place => place.method))) {
    const option = node('option', method);
    option.value = method;
    el('method').append(option);
  }
  el('method').addEventListener('change', event => showLocations(pokemon.locations, event.target.value));
  showLocations(pokemon.locations);
  showGrowth(pokemon, data, growth);
  showIntroduction(pokemon);
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
    if (!Object.hasOwn(data, id)) throw new Error('这个编号尚未收录，请返回宝可梦列表查找。');
    const record = data[id];
    if (record.canonicalId && record.canonicalId !== record.id) {
      location.replace('pokemons/' + record.canonicalId + '/');
      return;
    }
    let growth = null;
    try {
      const response = await fetch('data/growth.json');
      if (response.ok) growth = await response.json();
    } catch (_) { /* Keep the basic detail page available if growth data fails. */ }
    render(record, data, growth);
  } catch (error) {
    el('status').hidden = true;
    el('error').hidden = false;
    el('error-message').textContent = error.message;
  }
}
load();
