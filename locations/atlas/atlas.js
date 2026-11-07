'use strict';
const el=id=>document.getElementById(id),ns='http://www.w3.org/2000/svg';
const search=el('atlas-search'),type=el('atlas-type'),encounters=el('atlas-encounters');
let places=[],selectedCell=null,zoom=1,showSafari=false,showCity=false;
const typeOrder=['城镇','野外','洞穴','室内','水域','水下','其他'];
function node(tag,text){const e=document.createElement(tag);if(text!==undefined)e.textContent=text;return e;}
function matches(){const words=search.value.trim().toLowerCase().split(/\s+/).filter(Boolean);return places.filter(p=>(!type.value||p.type===type.value)&&(!encounters.value||(encounters.value==='yes'?p.pokemonCount>0:p.pokemonCount===0))&&words.every(word=>[p.name,p.foreign,p.mapId].join(' ').toLowerCase().includes(word)));}
function isCity(place){return place.name.startsWith('宾利市');}
function isSafari(place){return place.name.startsWith('狩猎地带');}
function selectSafari(event,place){
 if(event.button!==0||event.metaKey||event.ctrlKey||event.shiftKey||event.altKey)return;
 event.preventDefault();const entry=places.find(p=>p.path===place.path)||place;
 search.value='';type.value='';encounters.value='';selectedCell=entry.cells?.[0]??null;showSafari=true;draw();
 el('atlas-safari-preview').scrollIntoView({block:'nearest'});
}
function selectCity(event,place){
 if(event.button!==0||event.metaKey||event.ctrlKey||event.shiftKey||event.altKey)return;
 event.preventDefault();search.value='';type.value='';encounters.value='';selectedCell=place.cells[0]??null;showSafari=false;showCity=true;draw();el('atlas-city-preview').scrollIntoView({block:'nearest'});
}
function card(place){const article=node('article');article.className='atlas-map-card';const thumb=node('a');thumb.className='atlas-map-thumb';thumb.href=place.path;thumb.setAttribute('aria-label','查看 '+place.name+' 地图');if(place.image){const img=node('img');img.src=place.image;img.alt='';img.loading='lazy';img.width=96;img.height=80;thumb.append(img);}else thumb.textContent='暂无地形图';const content=node('div'),title=node('h3'),link=node('a',place.name);link.href=place.path;if(isSafari(place)){thumb.addEventListener('click',e=>selectSafari(e,place));}if(isCity(place))thumb.addEventListener('click',e=>selectCity(e,place));title.append(link);content.append(title,node('p',place.type+' · 地图 '+place.mapId+(place.size?' · '+place.size.join(' × ')+' 格':'')));
 if(place.note)content.append(Object.assign(node('p',place.note),{className:'atlas-entry-note'}));
 if(place.connections.length){const links=node('nav');links.className='atlas-connections';links.setAttribute('aria-label',place.name+'的直接连接');for(const neighbor of place.connections){const a=node('a',neighbor.name);a.href=neighbor.path;if(isSafari(neighbor))a.addEventListener('click',e=>selectSafari(e,neighbor));links.append(a);}content.append(links);}else if(place.methods.length)content.append(node('p',place.methods.join(' · ')));
 if(!place.methods.length)content.append(node('p','无野外遇敌记录'));
 article.append(thumb,content);return article;
}
function markers(filtered){const svg=el('atlas-markers');svg.replaceChildren();const cells=new Map();for(const place of filtered)for(const cell of place.cells){if(!cells.has(cell))cells.set(cell,[]);cells.get(cell).push(place);}
 for(const [cell,entries] of cells){const a=document.createElementNS(ns,'a'),rect=document.createElementNS(ns,'rect'),title=document.createElementNS(ns,'title');a.setAttribute('href',entries[0].path);a.setAttribute('aria-label',entries.map(p=>p.name).join('、'));a.setAttribute('aria-current',String(selectedCell===cell));title.textContent=entries.map(p=>p.name).join('、');const x=(36+8*(cell%22))*828/240,y=(36+8*Math.floor(cell/22))*828/240;for(const [key,value] of Object.entries({x:x-12,y:y-12,width:24,height:24,rx:4}))rect.setAttribute(key,value);a.append(title,rect);a.addEventListener('click',event=>{event.preventDefault();selectedCell=selectedCell===cell?null:cell;showSafari=selectedCell!==null&&entries.some(isSafari);showCity=selectedCell!==null&&entries.some(isCity);draw();});svg.append(a);}
}
function draw(){const filtered=matches();if(selectedCell!==null&&!filtered.some(p=>p.cells.includes(selectedCell))){selectedCell=null;showSafari=false;showCity=false;}const visible=selectedCell===null?filtered:filtered.filter(p=>p.cells.includes(selectedCell));if(!visible.some(isSafari))showSafari=false;if(!visible.some(isCity))showCity=false;window.cityMap.setVisible(showCity);el('atlas-safari-preview').hidden=!showSafari;document.querySelector('.atlas-world-panel').classList.toggle('has-safari',showSafari||showCity);markers(filtered);
 el('atlas-selection-title').textContent=selectedCell===null?'全部区域':'所选区域';el('atlas-selection-count').textContent=visible.length+' 处地点';el('atlas-clear-region').hidden=selectedCell===null;
 const fragment=document.createDocumentFragment();for(const label of typeOrder){const entries=visible.filter(p=>p.type===label);if(!entries.length)continue;const section=node('section');section.className='atlas-map-group';section.append(node('h2',label));for(const place of entries)section.append(card(place));fragment.append(section);}el('atlas-results').replaceChildren(fragment);el('atlas-empty').hidden=visible.length!==0;el('atlas-status').textContent='显示 '+visible.length+' / '+places.length+' 处地点 · '+filtered.filter(p=>p.cells.length).length+' 处已标在区域图上';
}
function setZoom(value){zoom=Math.max(.75,Math.min(2.5,value));el('atlas-world').style.width=(zoom*100)+'%';}
async function load(){try{const response=await fetch('data/atlas.json');if(!response.ok)throw Error('地图数据加载失败，请刷新重试。');places=await response.json();for(const label of typeOrder.filter(label=>places.some(p=>p.type===label))){const option=node('option',label);option.value=label;type.append(option);}draw();}catch(e){el('atlas-status').textContent=e.message;}}
search.addEventListener('input',draw);type.addEventListener('change',draw);encounters.addEventListener('change',draw);
el('atlas-reset').onclick=()=>{search.value='';type.value='';encounters.value='';selectedCell=null;showSafari=false;showCity=false;draw();};
el('atlas-clear-region').onclick=()=>{selectedCell=null;showSafari=false;showCity=false;draw();};
el('atlas-zoom-in').onclick=()=>setZoom(zoom+.25);el('atlas-zoom-out').onclick=()=>setZoom(zoom-.25);el('atlas-fit').onclick=()=>setZoom(1);
load();

