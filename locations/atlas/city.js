'use strict';
(()=>{
 const byId=id=>document.getElementById(id),panel=byId('atlas-city-preview'),stage=byId('city-map-stage'),viewport=byId('city-map-viewport');
 let data=null,pending=null,zoom=1,selected=null;
 function updateLayers(){
  const active=new Set([...panel.querySelectorAll('[data-city-layer]:checked')].map(input=>input.dataset.cityLayer));
  for(const point of panel.querySelectorAll('[data-city-kind]'))point.hidden=!active.has(point.dataset.cityKind);
  const shown=data?data.pois.filter(p=>active.has(p.kind)).length:0;byId('city-layer-status').textContent='显示 '+shown+' 个位置';
  if(selected&&!active.has(selected.kind)){selected=null;for(const button of panel.querySelectorAll('.city-poi.selected'))button.classList.remove('selected');byId('city-selected-poi').textContent='选择地图标记或下方名称，查看位置说明。';}
 }
 function selectPoi(poi){
  selected=poi;for(const button of panel.querySelectorAll('.city-poi'))button.classList.toggle('selected',button.dataset.poi===poi.id);
  byId('city-selected-poi').textContent=poi.name+' · '+poi.description;
  const w=stage.clientWidth,h=stage.clientHeight;viewport.scrollTo({left:Math.max(0,poi.x/data.width*w-viewport.clientWidth/2),top:Math.max(0,poi.y/data.height*h-viewport.clientHeight/2),behavior:'smooth'});
 }
 function draw(){
  byId('city-map-image').src=data.image;const markers=byId('city-map-markers'),legend=byId('city-poi-list');markers.replaceChildren();legend.replaceChildren();
  const prefixes={gym:'馆',clown:'丑',center:'中',daycare:'饲'};
  for(const poi of data.pois){
   const marker=document.createElement('button');marker.type='button';marker.className='city-poi';marker.dataset.cityKind=poi.kind;marker.dataset.poi=poi.id;marker.textContent=prefixes[poi.kind]+poi.label;marker.style.left=(poi.x/data.width*100)+'%';marker.style.top=(poi.y/data.height*100)+'%';marker.setAttribute('aria-label',poi.name+'，'+poi.description);marker.title=poi.name+' · '+poi.description;marker.onclick=()=>selectPoi(poi);markers.append(marker);
   const entry=document.createElement('button');entry.type='button';entry.className='city-poi-entry';entry.dataset.cityKind=poi.kind;entry.textContent=prefixes[poi.kind]+poi.label+' · '+poi.name;entry.onclick=()=>selectPoi(poi);legend.append(entry);
  }
  byId('city-map-status').hidden=true;byId('city-map-content').hidden=false;updateLayers();
 }
 async function ensureLoaded(){
  if(data)return;if(pending)return pending;
  pending=(async()=>{try{const response=await fetch('data/binsoville-city.json');if(!response.ok)throw Error('城市地图加载失败，请重新选择宾利市。');data=await response.json();draw();}catch(e){byId('city-map-status').textContent=e.message;}finally{pending=null;}})();return pending;
 }
 function setZoom(value){zoom=Math.max(1,Math.min(8,value));stage.style.width=(zoom*100)+'%';byId('city-map-scale').textContent=Math.round(zoom*100)+'%';}
 for(const input of panel.querySelectorAll('[data-city-layer]'))input.addEventListener('change',updateLayers);
 byId('city-zoom-in').onclick=()=>setZoom(zoom*1.5);byId('city-zoom-out').onclick=()=>setZoom(zoom/1.5);byId('city-zoom-fit').onclick=()=>{setZoom(1);viewport.scrollTo(0,0);};
 window.cityMap={setVisible(visible){panel.hidden=!visible;if(visible)ensureLoaded();}};
})();
