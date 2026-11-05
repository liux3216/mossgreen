function mapArt(id){
 const [src,w,h,land,water]=mapData[id];
 const box=elt('span'), img=elt('img');
 box.className='map-art';img.src=src.startsWith('locations/')?src:'data:image/webp;base64,'+src;
 img.alt='';img.loading='lazy';img.decoding='async';
 box.append(img);
 if(land.length||water.length){
  const ns='http://www.w3.org/2000/svg';
  const svg=document.createElementNS(ns,'svg');
  svg.setAttribute('viewBox','0 0 '+w+' '+h);
  svg.setAttribute('preserveAspectRatio','none');
  svg.setAttribute('aria-hidden','true');
  for(const [indices,color] of [[land,'#ffc335'],[water,'#34bcff']]){
   if(!indices.length)continue;
   const path=document.createElementNS(ns,'path'),runs=[];
   for(let i=0;i<indices.length;){
    const first=indices[i],y=Math.floor(first/w);let end=first;
    while(++i<indices.length&&indices[i]===end+1&&Math.floor(indices[i]/w)===y)end++;
    runs.push('M'+(first%w)+' '+y+'h'+(end-first+1)+'v1h-'+(end-first+1)+'z');
   }
   path.setAttribute('d',runs.join(''));
   path.setAttribute('fill',color);path.setAttribute('fill-opacity','.47');svg.append(path);
  }
  box.append(svg);
 }
 return box;
}
function preview(map,id){
 if(!mapData[id])return null;
 const b=elt('button');b.type='button';b.className='map-preview';
 b.setAttribute('aria-label','放大 '+map+' 地图');
 b.append(mapArt(id));
 b.addEventListener('click',()=>{
  mapTitle.textContent=map+' · '+id;full.classList.remove('hidden-overlay');
  const art=mapArt(id);art.querySelector('img').loading='eager';full.replaceChildren(art);
  const [,w,h,land,water]=mapData[id];
  legend.replaceChildren();
  if(land.length||water.length){
   const label=elt('label'), toggle=elt('input');
   toggle.type='checkbox';toggle.checked=true;
   toggle.addEventListener('change',()=>full.classList.toggle('hidden-overlay',!toggle.checked));
   const text=[land.length?'黄色：陆地遇敌格':'',water.length?'蓝色：水域遇敌格':''].filter(Boolean).join(' · ');
   label.append(toggle,document.createTextNode(text));legend.append(label,elt('p',w+' × '+h+' 格 · 按 ROM 的初始地块标记'));
  }else legend.textContent=w+' × '+h+' 格 · 这张地图未识别到可高亮的遇敌地块。遇敌表存在不代表地图里有对应地块。';
  dialog.showModal();
 });
 return b;
}
function atlasArt(id){
 const [cells]=atlasLocations[id]||[[]];
 const crop=elt('span'),box=elt('span'),img=elt('img');
 crop.className='atlas-crop';box.className='map-art';
 img.src=atlasSrc;img.alt='';img.loading='lazy';img.decoding='async';img.width=828;img.height=551;
 box.append(img);
 if(cells.length){
  const ns='http://www.w3.org/2000/svg',svg=document.createElementNS(ns,'svg');
  svg.setAttribute('viewBox','0 0 828 551');svg.setAttribute('aria-hidden','true');
  for(const cell of cells){
   // The ROM cursor grid starts at (36, 36) on the 240-pixel-wide screen.
   const cx=(36+8*(cell%22))*828/240,cy=(36+8*Math.floor(cell/22))*828/240;
   for(const style of ['atlas-marker','atlas-ring']){
    const rect=document.createElementNS(ns,'rect');
    rect.setAttribute('class',style);rect.setAttribute('x',cx-12);rect.setAttribute('y',cy-12);
    rect.setAttribute('width',24);rect.setAttribute('height',24);rect.setAttribute('rx',4);
    svg.append(rect);
   }
  }
  box.append(svg);
 }
 crop.append(box);return crop;
}
function atlasPreview(map,id){
 if(!atlasLocations[id])return null;
 const [cells,note]=atlasLocations[id];
 const button=elt('button');button.type='button';button.className='map-preview';
 button.setAttribute('aria-label','放大 '+map+' 的区域总图');
 button.append(atlasArt(id));
 button.addEventListener('click',()=>{
  mapTitle.textContent=map+' · 区域总图';full.classList.remove('hidden-overlay');
  const art=atlasArt(id);art.querySelector('img').loading='eager';full.replaceChildren(art);
  legend.textContent=cells.length?(note?'黄色框标出'+note+'，并非该子地图的独立图标。':'黄色框标出游戏区域地图上的对应位置。同一区域的楼层或南北段可能共用一处标记。'):note+'，可打开地点详图查看地形。';
  dialog.showModal();
 });
 return button;
}
function figure(button,text){
 const f=elt('figure');f.append(button,elt('figcaption',text));return f;
}
