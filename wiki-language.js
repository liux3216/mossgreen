'use strict';

(() => {
  const root = document.documentElement;
  const storageKey = 'mossgreen-language';
  const english = 'en';
  const chinese = 'zh-CN';
  const containsChinese = /[\u3400-\u9fff]/;
  const attributes = ['aria-label', 'alt', 'title', 'placeholder', 'content'];
  const localizesPage = !document.body.hasAttribute('data-language-managed');
  const originalText = new WeakMap();
  const originalAttributes = new WeakMap();
  let dictionary;
  let request;
  let selection = 0;
  let buttons = [];

  function savedLanguage() {
    const urlLanguage = new URLSearchParams(location.search).get('lang');
    if (urlLanguage === english || urlLanguage === chinese) return urlLanguage;
    try {
      if (localStorage.getItem(storageKey) === english) return english;
    } catch {
      // The URL still works when storage is disabled.
    }
    return chinese;
  }

  function saveLanguage(language) {
    try {
      localStorage.setItem(storageKey, language);
    } catch {
      // The URL still works when storage is disabled.
    }
  }

  function loadDictionary() {
    request ??= fetch('data/wiki.en.json', {cache: 'no-cache'}).then(response => {
      if (!response.ok) throw new Error('English translation unavailable');
      return response.json();
    }).then(data => { dictionary = data; return data; }).catch(error => {
      request = null;
      throw error;
    });
    return request;
  }

  const countLabels = {
    '件道具': 'items', '个学习机': 'machines', '个招式': 'moves',
    '个特性': 'abilities', '个地点': 'locations', '处地点': 'locations',
    '条获取记录': 'acquisition records', '项获取记录': 'acquisition records',
    '个地图分区': 'map areas', '个位置': 'markers', '种遇敌方式': 'encounter methods',
    '个形态': 'forms', '个条目': 'entries', '格': 'tiles',
  };

  function translate(text) {
    if (!dictionary || !containsChinese.test(text)) return text;
    const source = text.trim();
    const replacement = lookup(source);
    return replacement === source ? text : text.replace(source, replacement);
  }

  function lookup(source) {
    if (Object.hasOwn(dictionary, source)) return dictionary[source];

    let match = source.match(/^显示 ([\d,]+) \/ ([\d,]+) (\S+?)(?: · (.+))?$/);
    if (match && countLabels[match[3]]) {
      const detail = match[4] ? ' · ' + lookup(match[4]) : '';
      return `Showing ${match[1]} of ${match[2]} ${countLabels[match[3]]}${detail}`;
    }
    match = source.match(/^(?:(?:显示|共) )?([\d,]+) (件道具|个学习机|个招式|个特性|个地点|处地点|条获取记录|项获取记录|个地图分区|个位置|种遇敌方式|个形态|个条目)$/);
    if (match) return match[1] + ' ' + countLabels[match[2]];
    match = source.match(/^查看全部 (\d+) 个形态$/);
    if (match) return 'View all ' + match[1] + ' forms';
    match = source.match(/^全部 (\d+) 项$/);
    if (match) return 'View all ' + match[1] + ' records';
    match = source.match(/^另 (\d+) 处$/);
    if (match) return match[1] + ' more locations';
    match = source.match(/^\d+ 处已标在区域图上$/);
    if (match) return source.split(' ')[0] + ' marked on the regional map';
    match = source.match(/^平面图按 (\d+) × (\d+) 格显示$/);
    if (match) return 'Map size: ' + match[1] + ' × ' + match[2] + ' tiles';
    match = source.match(/^(\d+ × \d+) 格(.*)$/);
    if (match) return match[1] + ' tiles' + (match[2] ? ' ' + lookup(match[2].trim()) : '');
    match = source.match(/^(地图|形态|分区|室内|配置) ([\d/]+(?: \/ \d+)?)$/);
    if (match) return ({地图:'Map',形态:'Form',分区:'Area',室内:'Interior',配置:'Layout'})[match[1]] + ' ' + match[2];
    match = source.match(/^([馆丑中饲])(\d+)$/);
    if (match) return dictionary[match[1]] + match[2];
    match = source.match(/^查看 (.+) 地图$/);
    if (match) return 'View map of ' + lookup(match[1]);
    match = source.match(/^放大 (.+?)( 地图| 的区域总图| 水域示意图)?$/);
    if (match) return 'Enlarge ' + lookup(match[1]) + (match[2] ? ' ' + lookup(match[2].trim()) : '');
    match = source.match(/^(.+) 地图，可滚动查看$/);
    if (match) return 'Scrollable map of ' + lookup(match[1]);
    match = source.match(/^(.+)的直接连接$/);
    if (match) return 'Locations connected to ' + lookup(match[1]);
    match = source.match(/^(.+)的游戏立绘$/);
    if (match) return lookup(match[1]) + ' in-game sprite';
    match = source.match(/^此形态采用(.+)的本体介绍。$/);
    if (match) return 'This form uses the Pokédex entry for ' + lookup(match[1]) + '.';
    match = source.match(/^对应招式编号：([\d、]+)$/);
    if (match) return 'Move IDs: ' + match[1].replaceAll('、', ', ');
    match = source.match(/^([TH]M\d{2})「([^」]+)」(.*)$/);
    if (match) {
      const suffix = match[3].match(/^可学习条目：(\d+)$/);
      const title = match[1] + ' ' + lookup(match[2]);
      if (suffix) return title + ' · ' + suffix[1] + ' compatible Pokémon';
      return title + (match[3] ? ' ' + lookup(match[3].trim()) : '');
    }
    match = source.match(/^([^、（）·，]+)（([^、（）·，]+)）$/);
    if (match) {
      const name = lookup(match[1]), form = lookup(match[2]);
      if (name !== match[1] || form !== match[2]) return name + ' (' + form + ')';
    }
    const separator = [' · ', ' / ', '／', '、', '，'].find(value => source.includes(value));
    if (separator) {
      const index = source.indexOf(separator);
      const left = source.slice(0, index).trim();
      const right = source.slice(index + separator.length).trim();
      const first = lookup(left);
      const rest = lookup(right);
      if (first !== left || rest !== right) {
        const joiner = ({ '／': ' / ', '、': ', ', '，': ', ' })[separator] || separator;
        return first + joiner + rest;
      }
      return source;
    }
    const sentences = source.split(/(?<=[。！？])\s+/);
    if (sentences.length > 1) return sentences.map(lookup).join(' ');
    return source;
  }

  const searchKey = value => String(value ?? '').normalize('NFKD').toLowerCase().replace(/\p{M}/gu, '').replace(/’/g, "'");
  const searchable = text => searchKey(text) + (dictionary ? ' ' + searchKey(translate(String(text ?? ''))) : '');
  const matches = (text, query) => searchable(text).includes(searchKey(query));
  const compare = (a, b) => root.lang === english
    ? translate(String(a)).localeCompare(translate(String(b)), english, { numeric: true })
    : String(a).localeCompare(String(b), 'zh-Hans');

  function translateText(node) {
    const past = originalText.get(node);
    const source = past?.rendered === node.data ? past.source : node.data;
    const rendered = root.lang === english ? translate(source) : source;
    if (rendered !== node.data) {
      const option = node.parentElement?.closest('option');
      if (option && !option.hasAttribute('value')) option.value = option.value;
      originalText.set(node, {source, rendered});
      node.data = rendered;
    }
  }

  function translateAttribute(element, name) {
    const current = element.getAttribute(name);
    if (current === null || (name === 'content' && !element.matches('meta[name="description"]'))) return;
    const saved = originalAttributes.get(element);
    const past = saved?.get(name);
    const source = past?.rendered === current ? past.source : current;
    const rendered = root.lang === english ? translate(source) : source;
    if (current !== rendered) {
      const history = saved || new Map();
      history.set(name, {source, rendered});
      originalAttributes.set(element, history);
      element.setAttribute(name, rendered);
    }
  }

  const ignored = 'script, style, [data-language-picker]';
  function translateTree(node) {
    if (node.nodeType === Node.TEXT_NODE) {
      if (!node.parentElement?.closest(ignored)) translateText(node);
      return;
    }
    if (node.nodeType !== Node.ELEMENT_NODE || node.matches(ignored)) return;
    for (const attribute of attributes) translateAttribute(node, attribute);
    for (const child of node.childNodes) translateTree(child);
  }

  const observer = new MutationObserver(records => {
    observer.disconnect();
    for (const record of records) {
      if (record.type === 'attributes') translateAttribute(record.target, record.attributeName);
      else if (record.type === 'characterData') translateTree(record.target);
      else for (const child of record.addedNodes) translateTree(child);
    }
    startObserver();
  });

  function startObserver() {
    observer.observe(root, {
      subtree: true, childList: true, characterData: true, attributes: true, attributeFilter: attributes,
    });
  }

  function showLanguage(language) {
    const previous = root.lang;
    root.lang = language;
    for (const button of buttons) button.setAttribute('aria-pressed', String(button.lang === language));
    const picker = document.querySelector('[data-language-picker]');
    if (picker) picker.setAttribute('aria-label', language === english ? 'Language' : '语言');
    if (localizesPage && (language === english || previous === english)) {
      observer.disconnect();
      translateTree(root);
      if (language === english) startObserver();
    }
    document.dispatchEvent(new CustomEvent('wiki-language-change', {detail: language}));
  }

  async function setLanguage(language, persistUrl) {
    const change = ++selection;
    if (language === english && localizesPage) {
      try {
        await loadDictionary();
      } catch {
        if (change === selection) {
          const picker = document.querySelector('[data-language-picker]');
          if (picker) picker.setAttribute('aria-label', 'English could not load. Select English to retry.');
        }
        return;
      }
    }
    if (change !== selection) return;
    saveLanguage(language);
    if (persistUrl) {
      const url = new URL(location.href);
      url.searchParams.set('lang', language);
      history.replaceState(history.state, '', url);
    }
    showLanguage(language);
  }

  const header = document.querySelector('.wiki-header');
  if (header) {
    const picker = document.createElement('div');
    picker.className = 'wiki-language';
    picker.dataset.languagePicker = '';
    picker.setAttribute('role', 'group');
    picker.setAttribute('aria-label', '语言');
    buttons = [[chinese, '中文'], [english, 'English']].map(([language, label]) => {
      const button = document.createElement('button');
      button.type = 'button';
      button.lang = language;
      button.textContent = label;
      button.addEventListener('click', () => setLanguage(language, true));
      picker.append(button);
      return button;
    });
    header.append(picker);
  }
  window.wikiLanguage = { matches, searchable, compare };
  const initial = savedLanguage();
  for (const button of buttons) button.setAttribute('aria-pressed', String(button.lang === initial));
  setLanguage(initial, false);
})();
