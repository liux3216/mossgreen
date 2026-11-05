'use strict';
const el=id=>document.getElementById(id);
const search=el('location-search'),method=el('location-method');
let locations=[],sortKey=null,direction=1;
function node(tag,text){const e=document.createElement(tag);if(text!==undefined)e.textContent=text;return e;}
function draw(){
 const words=search.value.trim().toLowerCase().split(/\s+/).filter(Boolean);
 const visible=locations.filter(place=>words.every(word=>[place.name,place.foreign,place.mapId,...place.pokemon.flatMap(p=>[p.name,String(p.id)])].join(' ').toLowerCase().includes(word))&&(!method.value||place.methods.includes(method.value)));
 if(sortKey)visible.sort((a,b)=>{const result=sortKey==='count'?a.pokemon.length-b.pokemon.length:a.name.localeCompare(b.name,'zh-Hans');return result*direction;});
 const fragment=document.createDocumentFragment();
 for(const place of visible){const row=node('tr'),name=node('td'),link=node('a',place.name);link.href='locations/'+place.anchor.replace(/^location-/,'')+'/';const id=node('small',place.mapId);id.className='location-id';name.append(link,id);const methods=node('td'),badges=node('div');badges.className='location-methods';for(const kind of place.methods)badges.append(node('span',kind));methods.append(badges);row.append(name,methods,node('td',String(place.pokemon.length)));fragment.append(row);}
 el('location-rows').replaceChildren(fragment);el('locations-status').textContent='显示 '+visible.length+' / '+locations.length+' 个地点';el('locations-empty').hidden=visible.length!==0;el('locations-table-wrap').hidden=visible.length===0;
 for(const th of document.querySelectorAll('th[data-sort]')){th.setAttribute('aria-sort',th.dataset.sort===sortKey?(direction===1?'ascending':'descending'):'none');th.querySelector('.locations-sort').textContent=th.dataset.sort===sortKey?(direction===1?'↑':'↓'):'↕';}
}
async function load(){try{const response=await fetch('data/locations.json');if(!response.ok)throw Error('地点数据加载失败，请刷新重试。');locations=await response.json();el('location-total').textContent=locations.length;for(const value of [...new Set(locations.flatMap(p=>p.methods))]){const option=node('option',value);option.value=value;method.append(option);}draw();}catch(e){el('locations-status').textContent=e.message;}}
search.addEventListener('input',draw);method.addEventListener('change',draw);
el('reset-locations').onclick=()=>{search.value='';method.value='';draw();search.focus();};
for(const th of document.querySelectorAll('th[data-sort]'))th.querySelector('button').onclick=()=>{if(sortKey===th.dataset.sort)direction*=-1;else{sortKey=th.dataset.sort;direction=1;}draw();};
load();
