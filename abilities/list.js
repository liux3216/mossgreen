'use strict';
const el=id=>document.getElementById(id);
const search=el('ability-search'),availability=el('ability-availability');
let abilities=[],sortKey='id',direction=1;
const expanded=new Set();
function node(tag,text){const e=document.createElement(tag);if(text!==undefined)e.textContent=text;return e;}
function pokemonLink(p){const a=node('a',p.name);a.href='pokemons/'+p.id+'/';return a;}
function createRows(ability){
 const row=node('tr');row.id='ability-'+ability.id;row.className='ability-row';
 const detail=node('tr');detail.id='ability-detail-'+ability.id;detail.className='ability-detail';detail.hidden=!expanded.has(ability.id);
 const name=node('td'),button=node('button',ability.name);button.type='button';button.className='ability-name';name.append(button);
 const preview=node('td');preview.className='ability-preview';
 for(const p of ability.pokemon.slice(0,2)){const line=node('div');line.append(pokemonLink(p));preview.append(line);}
 if(!ability.pokemon.length)preview.append(node('div','暂无已收录的宝可梦'));
 const more=node('button',ability.pokemon.length+' 个形态 · '+new Set(ability.locations.map(p=>p.mapId)).size+' 个地点');more.type='button';preview.append(more);
 for(const b of [button,more]){b.setAttribute('aria-controls',detail.id);b.setAttribute('aria-expanded',String(!detail.hidden));b.onclick=()=>{const open=!expanded.has(ability.id);if(open)expanded.add(ability.id);else expanded.delete(ability.id);detail.hidden=!open;for(const b of [button,more])b.setAttribute('aria-expanded',String(open));if(open)history.replaceState(null,'','abilities/#ability-'+ability.id);};}
 row.append(node('td',String(ability.id)),name,node('td',ability.description),preview);
 const cell=node('td');cell.colSpan=4;cell.append(node('h2',ability.name),node('p',ability.description),node('h3','拥有此特性的宝可梦'));
 if(ability.pokemon.length){const grid=node('div');grid.className='ability-holders';for(const p of ability.pokemon){const a=pokemonLink(p);a.append(node('small',p.dex?'#'+p.dex:'未分配图鉴编号'));grid.append(a);}cell.append(grid);}else cell.append(node('p','暂无已收录的宝可梦。'));
 cell.append(node('h3','野外分布'));
 if(ability.locations.length){cell.append(node('p','以下地点可遇到拥有此特性的宝可梦，同一种宝可梦也可能拥有其他特性。'));const grid=node('div');grid.className='ability-locations';for(const p of ability.locations){const a=node('a',p.name);a.href='locations/'+p.anchor.replace(/^location-/,'')+'/';a.append(node('small',p.method+' · '+p.pokemonCount+' 个形态'));grid.append(a);}cell.append(grid);}else cell.append(node('p','暂无相关野外随机遇敌记录。'));
 detail.append(cell);return [row,detail];
}
function draw(){
 const query=search.value.trim().toLowerCase(),number=query.match(/^#?(\d+)$/);
 const visible=abilities.filter(a=>(!query||(number?a.id===Number(number[1]):[a.name,a.description,...a.pokemon.map(p=>p.name)].some(v=>v.toLowerCase().includes(query))))&&(!availability.value||(availability.value==='wild'?a.locations.length>0:a.locations.length===0)));
 visible.sort((a,b)=>{const av=a[sortKey],bv=b[sortKey];return (typeof av==='number'?av-bv:String(av).localeCompare(String(bv),'zh-Hans'))*direction||a.id-b.id;});
 const fragment=document.createDocumentFragment();for(const ability of visible)fragment.append(...createRows(ability));el('ability-rows').replaceChildren(fragment);
 el('abilities-status').textContent='显示 '+visible.length+' / '+abilities.length+' 个特性';el('abilities-empty').hidden=visible.length!==0;el('abilities-table-wrap').hidden=visible.length===0;
 for(const th of document.querySelectorAll('th[data-sort]')){th.setAttribute('aria-sort',th.dataset.sort===sortKey?(direction===1?'ascending':'descending'):'none');th.querySelector('.ability-sort').textContent=th.dataset.sort===sortKey?(direction===1?'↑':'↓'):'↕';}
}
function followHash(){const match=location.hash.match(/^#ability-(\d+)$/);if(!match)return;const id=Number(match[1]);if(!abilities.some(a=>a.id===id))return;search.value='#'+id;availability.value='';expanded.add(id);draw();}
async function load(){try{const response=await fetch('data/abilities.json');if(!response.ok)throw Error('特性数据加载失败，请刷新重试。');abilities=await response.json();el('ability-total').textContent=abilities.length;draw();followHash();}catch(e){el('abilities-status').textContent=e.message;}}
search.addEventListener('input',draw);availability.addEventListener('change',draw);
el('reset-abilities').onclick=()=>{search.value='';availability.value='';draw();search.focus();};
for(const th of document.querySelectorAll('th[data-sort]'))th.querySelector('button').onclick=()=>{if(sortKey===th.dataset.sort)direction*=-1;else{sortKey=th.dataset.sort;direction=1;}draw();};
window.addEventListener('hashchange',followHash);load();
