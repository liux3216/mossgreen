'use strict';
const elt=(tag,text)=>{const e=document.createElement(tag);if(text!==undefined)e.textContent=text;return e;};
const dialog=document.querySelector('#map-dialog'),full=document.querySelector('#map-full'),mapTitle=document.querySelector('#map-title'),legend=document.querySelector('#map-legend');
let mapData={},atlasLocations={},atlasSrc='locations/assets/region.png',place;
function drawConnections(){
 const connections=place.connections||[],nav=document.querySelector('#connected-locations');
 for(const connection of connections){
  const a=elt('a');a.href=connection.path;a.className='connected-location';
  const identity=elt('span');identity.className='connected-location-info';
  identity.append(elt('strong',connection.name),elt('small',connection.routes.join(' · ')));
  const arrow=elt('span','→');arrow.className='connected-location-arrow';arrow.setAttribute('aria-hidden','true');
  a.append(identity,arrow);nav.append(a);
 }
 document.querySelector('#connections-empty').hidden=connections.length>0;
 const note=document.querySelector('#connections-note');note.hidden=!connections.length;
 note.textContent=connections.some(c=>c.routes.includes('返回入口'))?'共用房间会返回进入时的地点。':'部分通路需要推进剧情或使用秘传招式。';
}
function drawSpecialAcquisitions(){
 const entries=place.specialAcquisitions||[],section=document.querySelector('#special-acquisitions');
 section.hidden=!entries.length;
 const body=document.querySelector('#special-acquisition-rows');
 for(const entry of entries){
  const row=elt('tr'),cell=elt('td'),identity=elt('div');identity.className='encounter-identity';
  const image=elt('img');image.src='data:image/png;base64,'+entry.sprite;image.alt='';image.width=40;image.height=40;image.loading='lazy';
  const link=elt('a',entry.pokemonName);link.href='pokemons/'+entry.pokemonId+'/';identity.append(image,link);cell.append(identity);
  const levels=entry.levelNote||entry.levels.map(([a,b])=>a===b?'Lv.'+a:'Lv.'+a+'–'+b).join('、')||'—';
  const condition=elt('td',entry.conditions.join(' '));condition.className='acquisition-condition';
  row.append(cell,elt('td',entry.method),elt('td',levels),condition);body.append(row);
 }
}
function drawEncounters(){
 const query=document.querySelector('#encounter-search').value.trim().toLowerCase(),method=document.querySelector('#encounter-method').value;
 const fragment=document.createDocumentFragment();let count=0;
 for(const entry of place.methods){
  if(method&&entry.name!==method)continue;
  const rows=entry.pokemon.filter(p=>!query||(p.name||'').toLowerCase().includes(query)||String(p.id).includes(query));
  if(!rows.length)continue;count+=rows.length;
  const section=elt('section');section.className='encounter-method';section.append(elt('h3',entry.name));
  const wrap=elt('div');wrap.className='location-table-wrap';const table=elt('table');table.className='location-encounter-table';
  const head=elt('thead'),headers=elt('tr');for(const title of ['宝可梦','属性','等级','出现比例']){const th=elt('th',title);th.scope='col';headers.append(th);}head.append(headers);table.append(head);
  const body=elt('tbody');for(const p of rows){const row=elt('tr'),name=elt('td'),identity=elt('div');identity.className='encounter-identity';if(p.sprite){const img=elt('img');img.src='data:image/png;base64,'+p.sprite;img.alt='';img.width=40;img.height=40;img.loading='lazy';identity.append(img);}if(p.known){const link=elt('a',p.name);link.href='pokemons/'+p.id+'/';identity.append(link);}else identity.append(elt('span',p.name||'未识别 #'+p.id));name.append(identity);
   const types=elt('td');for(const type of p.types){const badge=elt('span',type);badge.className='pokedex-type';badge.dataset.type=type;types.append(badge);}const levels=p.levels.map(([low,high])=>low===high?'Lv.'+low:'Lv.'+low+'–'+high).join('、');row.append(name,types,elt('td',levels),elt('td',p.chance+'%'));body.append(row);
  }table.append(body);wrap.append(table);section.append(wrap);fragment.append(section);
 }
 document.querySelector('#location-encounters').replaceChildren(fragment);document.querySelector('#encounters-empty').hidden=count>0;document.querySelector('#encounters-empty').textContent=place.methods.length?'没有找到对应的宝可梦。':'此地点没有野外随机遇敌记录。';
}
async function load(){const status=document.querySelector('#location-status');try{
 const response=await fetch('locations/data/'+document.body.dataset.location+'.json');if(!response.ok)throw Error('地点资料加载失败，请刷新重试。');place=await response.json();
 if(place.map){mapData[place.mapId]=place.map;mapData[place.mapId][0]=place.map[0];}if(place.atlas)atlasLocations[place.mapId]=place.atlas;
 document.querySelector('#location-meta').textContent='地图 '+place.mapId+(place.foreign?' · '+place.foreign:'')+(place.methods.length?' · '+place.methods.length+' 种遇敌方式':' · 无野外遇敌记录');
 const maps=document.querySelector('#location-maps');for(const [label,button] of [['区域总图',atlasPreview(place.name,place.mapId)],['地点详图',preview(place.name,place.mapId)]]){if(!button)continue;const card=elt('section');card.className='location-map-card';card.append(elt('h2',label));if(label==='地点详图'){const [,w,h]=place.map;button.style.width=Math.min(320,320*w/h)+'px';}card.append(button);if(label==='地点详图')card.append(elt('p',place.methods.length?'点击放大，可切换遇敌格高亮。':'点击放大查看地图。'));maps.append(card);}
 const images=[...maps.querySelectorAll('img')];
 await Promise.all(images.map(img=>{img.loading='eager';return img.decode().catch(()=>{});}));
 drawConnections();
 drawSpecialAcquisitions();
 if(place.related.length){document.querySelector('#related-section').hidden=false;for(const related of place.related){const a=elt('a',related.name);a.href=related.path;document.querySelector('#related-locations').append(a);}}
 document.querySelector('.location-filters').hidden=!place.methods.length;document.querySelector('.list-footer p').hidden=!place.methods.length;
 const method=document.querySelector('#encounter-method');for(const entry of place.methods){const option=elt('option',entry.name);option.value=entry.name;method.append(option);}method.addEventListener('change',drawEncounters);document.querySelector('#encounter-search').addEventListener('input',drawEncounters);drawEncounters();status.hidden=true;document.querySelector('#location-content').hidden=false;
 if(location.hash==='#special-acquisitions'&&!document.querySelector('#special-acquisitions').hidden)requestAnimationFrame(()=>document.querySelector('#special-acquisitions').scrollIntoView());
 }catch(e){status.textContent=e.message;}}
load();
