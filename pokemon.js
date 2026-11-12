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
    link.href = (place.path || 'locations/' + place.anchor.replace(/^location-/, '') + '/') + (place.kind ? '#special-acquisitions' : '');
    location.append(link, node('small', '地图 ' + place.mapId));
    if (place.entrances?.length) {
      const entry = place.entrances.find(e => e.name === place.preferredEntrance) || place.entrances[0];
      const hint = node('small', '入口：'), entrance = node('a', entry.name);
      entrance.href = entry.path; hint.append(entrance, document.createTextNode(entry.method === '挖洞' ? ' · 挖洞' : ''));
      location.append(hint);
    }
    const levels = place.levelNote || place.levels.map(([low, high]) =>
      low === high ? 'Lv.' + low : 'Lv.' + low + '–' + high
    ).join('、') || '—';
    const condition = node('td', place.kind ? place.conditions.join(' ') : place.chance + '%');
    if (place.kind) { row.className = 'special-acquisition'; condition.className = 'acquisition-condition'; }
    row.append(location, node('td', place.method), node('td', levels), condition);
    fragment.append(row);
  }
  if (!visible.length) {
    const row = node('tr');
    const cell = node('td', '暂无直接获取记录，可查看上方进化链。');
    cell.colSpan = 4;
    row.append(cell);
    fragment.append(row);
  }
  el('locations').replaceChildren(fragment);
  const maps = new Set(visible.map(place => place.mapId)).size;
  el('location-count').textContent = maps + ' 个地图分区 · ' + visible.length + ' 条获取记录';
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
  const availableEdges = growth.evolutions.filter(edge => {
    const special = data[edge.from]?.catalogStatus === 'special-record' || data[edge.to]?.catalogStatus === 'special-record';
    return !special || pokemon.catalogStatus === 'special-record';
  });
  const family = new Set([pokemon.id]);
  let changed = true;
  while (changed) {
    changed = false;
    for (const edge of availableEdges) {
      if (family.has(edge.from) || family.has(edge.to)) {
        for (const id of [edge.from, edge.to]) {
          if (!family.has(id)) { family.add(id); changed = true; }
        }
      }
    }
  }
  const edges = availableEdges.filter(e => family.has(e.from) && family.has(e.to));
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
      if (!path.length || !path.some(edge => edge.from === pokemon.id || edge.to === pokemon.id)) continue;
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
  const evolutionNotes = new Set([...family].flatMap(id => growth.species[id]?.evolutionNotes || []));
  for (const text of evolutionNotes) {
    const note = node('p', text);
    note.className = 'muted small evolution-note';
    host.append(note);
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
    const response = await fetch('data/introductions.json', { cache: 'no-store' });
    if (!response.ok) throw new Error('Introduction unavailable');
    const data = await response.json();
    const mapping = data.pokemon[pokemon.id];
    const entry = mapping && data.species[mapping.speciesId];
    if (!entry) {
      el('dex-entry-text').textContent = '暂无可核实的图鉴介绍。';
      return;
    }
    el('dex-entry-text').textContent = entry.text.replace(/[０-９]/g, digit =>
      String.fromCharCode(digit.charCodeAt(0) - 0xFEE0));
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
function render(pokemon, data, growth, special, specialFailed) {
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
  const related = (pokemon.relatedIds || []).map(id => data[id]).filter(Boolean);
  const forms = related.length ? related : (pokemon.formIds || [pokemon.id]).map(id => data[id]).filter(Boolean);
  const currentFormIndex = forms.findIndex(form => form.id === pokemon.id);
  if (forms.length > 1) {
    el('form-section').hidden = false;
    el('form-heading').textContent = related.length ? '相关记录' : '形态';
    el('form-options').setAttribute('aria-label', related.length ? '查看宝可梦相关记录' : '切换宝可梦形态');
    el('form-label').hidden = !!related.length && !pokemon.catalogNote;
    el('form-label').textContent = pokemon.catalogNote || (related.length ? '' : '形态 ' + (currentFormIndex + 1) + ' / ' + forms.length);
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
      description.append(node('strong', form.name + ' · ' + (related.length ? form.catalogLabel : '形态 ' + (index + 1))));
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
  const acquisitions = [...pokemon.locations, ...(special?.pokemon[pokemon.id] || [])];
  for (const method of new Set(acquisitions.map(place => place.method))) {
    const option = node('option', method);
    option.value = method;
    el('method').append(option);
  }
  el('method').addEventListener('change', event => showLocations(acquisitions, event.target.value));
  showLocations(acquisitions);
  el('special-acquisition-status').hidden = !specialFailed;
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
    const optional = await Promise.allSettled(['data/growth.json', 'data/special-acquisitions.json'].map(async path => {
      const response = await fetch(path);
      if (!response.ok) throw new Error('资料加载失败');
      return response.json();
    }));
    const growth = optional[0].status === 'fulfilled' ? optional[0].value : null;
    const special = optional[1].status === 'fulfilled' ? optional[1].value : null;
    render(record, data, growth, special, !special);
  } catch (error) {
    el('status').hidden = true;
    el('error').hidden = false;
    el('error-message').textContent = error.message;
  }
}
load();
