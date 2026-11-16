'use strict';
const search = document.getElementById('pokemon-search');
const typeFilter = document.getElementById('pokemon-type');
const results = document.getElementById('pokemon-grid');
const body = document.getElementById('pokemon-rows');
const sortHeaders = [...results.querySelectorAll('th[data-sort]')];
const collators = {
  'zh-CN': new Intl.Collator('zh-Hans-CN-u-co-pinyin'),
  en: new Intl.Collator('en'),
};
const englishTypes = {
  '一般': 'Normal', '格斗': 'Fighting', '飞行': 'Flying', '毒': 'Poison',
  '地面': 'Ground', '岩石': 'Rock', '虫': 'Bug', '幽灵': 'Ghost', '钢': 'Steel',
  '火': 'Fire', '水': 'Water', '草': 'Grass', '电': 'Electric', '超能力': 'Psychic',
  '冰': 'Ice', '龙': 'Dragon', '恶': 'Dark', '妖精': 'Fairy', '未知': 'Unknown',
};
const englishMethods = {
  '草丛／洞穴': 'Grass / Cave', '冲浪': 'Surfing', '旧钓竿': 'Old Rod',
  '好钓竿': 'Good Rod', '厉害钓竿': 'Super Rod', '碎岩': 'Rock Smash',
};
const localizedCopy = ['text', 'aria-label', 'placeholder', 'title', 'content'].flatMap(attribute => {
  const source = attribute === 'text' ? 'data-en' : 'data-en-' + attribute;
  return [...document.querySelectorAll('[' + source + ']')].map(node => ({
    node,
    attribute,
    en: node.getAttribute(source),
    zh: attribute === 'text' ? node.textContent : node.getAttribute(attribute),
  }));
});
let language = 'zh-CN';
let translations;

function updateLanguage(next) {
  language = next;
  document.documentElement.lang = language;
  for (const { node, attribute, en, zh } of localizedCopy) {
    const value = language === 'en' ? en : zh;
    if (attribute === 'text') node.textContent = value;
    else node.setAttribute(attribute, value);
  }
  for (const option of typeFilter.options) {
    if (option.value) option.textContent = typeName(option.value);
  }
}

function text(zh, en) {
  return language === 'en' ? en : zh;
}

function pokemonName(record) {
  return text(record.name, translations?.pokemon[record.name] ?? record.name);
}

function typeName(type) {
  return text(type, englishTypes[type] ?? type);
}

function placeLabel(place) {
  if (language === 'zh-CN') return place.name + '（' + place.method + '）';
  const name = translations.locations[place.name] ?? place.name;
  return name + ' · ' + (englishMethods[place.method] ?? place.method);
}

function searchKey(value) {
  return value.toLowerCase().normalize('NFD').replace(/\p{M}/gu, '').replace(/’/g, "'");
}
const sortValues = {
  name: pokemonName,
  type: record => verified(record) && record.types.length ? record.types.map(typeName).join(' ') : null,
  total: record => record.statTotal,
  locations: record => record.locations.length,
};
let sortKey = '';
let direction = 1;
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
  const displayName = pokemonName(record);
  const name = element('a', displayName);
  name.href = imageLink.href;
  name.className = 'pokemon-name';
  nameCell.append(name);
  if (record.otherForms.length) {
    const forms = element('details');
    forms.className = 'catalog-forms';
    const count = record.otherForms.length;
    forms.append(element('summary', text(`其他 ${count} 个形态`, `${count} other ${count === 1 ? 'form' : 'forms'}`)));
    record.otherForms.forEach((form, index) => {
      const formName = pokemonName(form);
      const label = formName === displayName ? formName + text(` · 形态 ${index + 2}`, ` · Form ${index + 2}`) : formName;
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
      const badge = element('span', typeName(type));
      badge.className = 'pokedex-type';
      badge.dataset.type = type;
      badges.append(badge);
    }
  } else badges.append(element('small', text('待核实', 'Unverified')));
  typeCell.append(badges);
  const locations = element('td');
  locations.className = 'location-preview';
  for (const place of record.locations.slice(0, 2)) {
    const link = element('a', placeLabel(place));
    link.href = 'locations/' + place.anchor.replace(/^location-/, '') + '/';
    locations.append(link);
  }
  if (!record.locations.length) locations.append(element('span', text('暂无野外遇敌记录', 'No wild encounters recorded')));
  if (record.locations.length > 2) {
    const count = record.locations.length;
    const more = element('a', text(`全部 ${count} 项`, `View all ${count} locations`));
    more.className = 'more-locations';
    more.href = 'pokemons/' + record.id + '/#encounters-heading';
    locations.append(more);
  }
  row.append(imageCell, number, nameCell, typeCell, element('td', String(record.statTotal ?? '—')), locations);
  return row;
}
function show(pokemon) {
  const query = searchKey(search.value.trim());
  const numberQuery = query.replace(/^#/, '');
  const visible = pokemon.filter(record =>
    ([record, ...record.otherForms].some(form => form.searchNames.some(name => name.includes(query))) ||
      (record.gameDexId && String(record.gameDexId).padStart(4, '0').includes(numberQuery))) &&
    (!typeFilter.value || [record, ...record.otherForms].some(form => verified(form) && form.types.includes(typeFilter.value)))
  );
  if (sortKey) {
    const value = sortValues[sortKey];
    visible.sort((a, b) => {
      const left = value(a);
      const right = value(b);
      if (left === null || right === null) return Number(left === null) - Number(right === null);
      return direction * (typeof left === 'number' ? left - right : collators[language].compare(left, right));
    });
  }
  const expanded = new Set([...body.querySelectorAll('.catalog-forms[open]')].map(forms => forms.closest('tr').dataset.pokemonId));
  body.replaceChildren(...visible.map(createRow));
  for (const id of expanded) {
    const forms = body.querySelector(`[data-pokemon-id="${id}"] .catalog-forms`);
    if (forms) forms.open = true;
  }
  results.hidden = visible.length === 0;
  empty.hidden = visible.length !== 0;
  status.textContent = text(
    `显示 ${visible.length} / ${pokemon.length} 个精灵条目 · 不同形态收在对应条目下`,
    `Showing ${visible.length} of ${pokemon.length} Pokémon entries · Alternate forms are grouped together`
  );
}
async function loadJson(path) {
  const response = await fetch(path, { cache: 'no-cache' });
  if (!response.ok) throw new Error('Could not load ' + path);
  return response.json();
}

async function load() {
  const translationRequest = loadJson('data/pokedex.en.json').catch(() => null);
  const pokemonRequest = loadJson('data/pokemon.json');
  try {
    const [englishData, data] = await Promise.all([translationRequest, pokemonRequest]);
    translations = englishData;
    if (!translations) updateLanguage('zh-CN');
    for (const record of Object.values(data)) {
      const englishName = translations?.pokemon[record.name];
      record.searchNames = (englishName ? [record.name, englishName] : [record.name]).map(searchKey);
    }
    const pokemon = Object.values(data)
      .filter(record => !record.catalogHidden && record.id === record.canonicalId && record.id === record.catalogPrimaryId)
      .map(record => ({
        ...record,
        otherForms: record.formIds.filter(id => id !== record.id).map(id => data[id]),
        statTotal: verified(record) ? Object.values(record.stats).reduce((sum, value) => sum + value, 0) : null,
        locations: [...new Map(record.locations.map(place => [place.anchor + ':' + place.method, place])).values()],
      }))
      .sort((a, b) => (a.gameDexId || Infinity) - (b.gameDexId || Infinity) || a.id - b.id);
    document.getElementById('entry-total').textContent = pokemon.length;
    const types = [...new Set(pokemon.filter(verified).flatMap(record => record.types))];
    for (const type of types) {
      const option = element('option', typeName(type));
      option.value = type;
      typeFilter.append(option);
    }
    for (const header of sortHeaders) {
      header.querySelector('button').addEventListener('click', () => {
        const key = header.dataset.sort;
        direction = sortKey === key ? -direction : 1;
        sortKey = key;
        results.querySelector('th[aria-sort]')?.removeAttribute('aria-sort');
        header.setAttribute('aria-sort', direction === 1 ? 'ascending' : 'descending');
        show(pokemon);
      });
    }
    search.addEventListener('input', () => show(pokemon));
    typeFilter.addEventListener('change', () => show(pokemon));
    document.getElementById('reset-filters').addEventListener('click', () => {
      search.value = '';
      typeFilter.value = '';
      show(pokemon);
    });
    document.addEventListener('wiki-language-change', () => {
      if (!translations) updateLanguage('zh-CN');
      show(pokemon);
    });
    show(pokemon);
  } catch {
    status.textContent = text('宝可梦图鉴加载失败，请刷新重试。', 'Could not load the Pokédex. Please reload this page.');
  }
}
document.addEventListener('wiki-language-change', event => updateLanguage(event.detail));
updateLanguage(document.documentElement.lang);
load();
