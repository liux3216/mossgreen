'use strict';
const byId=id=>document.getElementById(id);
const search=byId('move-search'),type=byId('move-type'),category=byId('move-category');
let moves=[],sortKey='id',direction=1;
const openMoves=new Set();
function deduplicateMoves(records){
 const groups=new Map();
 for(const move of records){if(!groups.has(move.name))groups.set(move.name,[]);groups.get(move.name).push(move);}
 return [...groups.values()].map(group=>{
  // Prefer a populated ROM slot; retain every ID for search and old links.
  const primary=[...group].sort((a,b)=>Number(b.dataAvailable)-Number(a.dataAvailable)||a.id-b.id)[0];
  const learners=new Map();
  for(const move of group)for(const learner of move.learners){
   if(!learners.has(learner.id))learners.set(learner.id,{...learner,levels:[]});
   const merged=learners.get(learner.id);merged.levels=[...new Set([...merged.levels,...learner.levels])].sort((a,b)=>a-b);
  }
  return {...primary,aliases:group.map(m=>m.id).sort((a,b)=>a-b),learners:[...learners.values()].sort((a,b)=>(a.dex??Infinity)-(b.dex??Infinity)||a.id-b.id)};
 });
}
function node(tag,text){const el=document.createElement(tag);if(text!==undefined)el.textContent=text;return el;}
function learnerLink(p){const a=node('a',p.name);a.href='pokemons/'+p.id+'/';return a;}
function toggleMove(move,row,detail,buttons){
 const open=!openMoves.has(move.id);if(open)openMoves.add(move.id);else openMoves.delete(move.id);
 detail.hidden=!open;for(const b of buttons)b.setAttribute('aria-expanded',String(open));
 if(open)history.replaceState(null,'','moves/#move-'+move.id);
}
function createRows(move){
 const row=node('tr');row.className='move-row';row.id='move-'+move.id;row.title='对应招式编号：'+move.aliases.join('、');
 const detail=node('tr');detail.className='move-details';detail.id='move-details-'+move.id;detail.hidden=!openMoves.has(move.id);
 const nameCell=node('td'),button=node('button',move.name);button.className='move-name';button.type='button';button.setAttribute('aria-expanded',String(!detail.hidden));button.setAttribute('aria-controls',detail.id);nameCell.append(button);
 const typeCell=node('td'),badge=node('span',move.dataAvailable?move.type:'—');badge.className=move.dataAvailable?'pokedex-type':'muted';badge.dataset.type=move.type;typeCell.append(badge);
 const categoryCell=node('td'),label=node('span',move.dataAvailable?move.category:'—');label.className=move.dataAvailable?'move-category':'muted';label.dataset.category=move.category;categoryCell.append(label);
 const preview=node('td');preview.className='learners-preview';
 const buttons=[button];
 if(!move.dataAvailable)preview.append(node('div','数值未设置'));
 for(const p of move.learners.slice(0,2)){const line=node('div');line.append(learnerLink(p),document.createTextNode(' · Lv.'+p.levels.join('、')));preview.append(line);}
 if(move.learners.length){const more=node('button',move.learners.length>2?'查看全部 '+move.learners.length+' 个形态':'查看升级习得');more.type='button';more.setAttribute('aria-controls',detail.id);more.setAttribute('aria-expanded',String(!detail.hidden));buttons.push(more);preview.append(more);}
 else preview.append(node('span','暂无升级习得记录'));
 for(const b of buttons)b.onclick=()=>toggleMove(move,row,detail,buttons);
 row.append(node('td',String(move.id)),nameCell,typeCell,categoryCell,node('td',move.power?String(move.power):'—'),node('td',move.accuracy?String(move.accuracy):'—'),node('td',move.dataAvailable?String(move.pp):'—'),preview);
 const cell=node('td');cell.colSpan=8;cell.append(node('h2',move.name+' · 升级习得'));
 if(move.learners.length){const grid=node('div');grid.className='learners-grid';for(const p of move.learners){const a=learnerLink(p);a.append(node('small',(p.dex?'#'+p.dex+' · ':'')+p.levels.map(l=>'Lv.'+l).join('、')));grid.append(a);}cell.append(grid);}
 else cell.append(node('p','暂无宝可梦通过升级学会此招式的记录。'));
 detail.append(cell);return [row,detail];
}
function draw(){
 const query=search.value.trim().toLowerCase();const idQuery=query.match(/^#?(\d+)$/);
 const filtered=moves.filter(m=>(!query||(idQuery?m.aliases.includes(Number(idQuery[1])):m.name.toLowerCase().includes(query)))&&(!type.value||(m.dataAvailable&&m.type===type.value))&&(!category.value||(m.dataAvailable&&m.category===category.value)));
 filtered.sort((a,b)=>{const av=a[sortKey],bv=b[sortKey];const n=typeof av==='number'?av-bv:String(av).localeCompare(String(bv),'zh-Hans');return n*direction||a.id-b.id;});
 const fragment=document.createDocumentFragment();for(const move of filtered)fragment.append(...createRows(move));byId('move-rows').replaceChildren(fragment);
 byId('moves-status').textContent='显示 '+filtered.length+' / '+moves.length+' 个招式';byId('moves-empty').hidden=filtered.length!==0;byId('moves-table-wrap').hidden=filtered.length===0;
 for(const th of document.querySelectorAll('th[data-sort]')){th.setAttribute('aria-sort',th.dataset.sort===sortKey?(direction===1?'ascending':'descending'):'none');th.querySelector('.sort-indicator').textContent=th.dataset.sort===sortKey?(direction===1?'↑':'↓'):'↕';}
}
function followHash(){const match=location.hash.match(/^#move-(\d+)$/);if(!match)return;const id=Number(match[1]);const move=moves.find(m=>m.aliases.includes(id));if(!move)return;search.value='#'+id;type.value='';category.value='';openMoves.add(move.id);draw();}
async function load(){try{const response=await fetch('data/moves.json');if(!response.ok)throw Error('招式数据加载失败，请刷新重试。');moves=deduplicateMoves(await response.json());byId('move-total').textContent=moves.length;for(const value of [...new Set(moves.map(m=>m.type))]){const o=node('option',value);o.value=value;type.append(o);}draw();followHash();}catch(e){byId('moves-status').textContent=e.message;}}
search.addEventListener('input',draw);type.addEventListener('change',draw);category.addEventListener('change',draw);
byId('reset-moves').onclick=()=>{search.value='';type.value='';category.value='';draw();search.focus();};
for(const th of document.querySelectorAll('th[data-sort]'))th.querySelector('button').onclick=()=>{if(sortKey===th.dataset.sort)direction*=-1;else{sortKey=th.dataset.sort;direction=1;}draw();};
window.addEventListener('hashchange',followHash);load();
