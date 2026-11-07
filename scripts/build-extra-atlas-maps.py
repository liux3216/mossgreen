"""Render the five connected Binsoville outdoor maps and verified points of interest.
Requires Pillow. Usage: python scripts/build-binsoville-city.py game.gba
"""
from pathlib import Path
import struct,json,sys,hashlib,re
from functools import lru_cache
from PIL import Image
root=Path(__file__).resolve().parent.parent
rom=Path(sys.argv[1]).read_bytes()
def raw(a,n):
 offset=a&0x1ffffff;return rom[offset:offset+n]
def words(a,n=1):return struct.unpack('<'+'I'*n,raw(a,4*n))
def halves(a,n):return struct.unpack('<'+'H'*n,raw(a,2*n))
def header(g,m):return words(words(0x3526a8+4*g)[0]+4*m)[0]
def lz(a):
 i=a&0x1ffffff;assert rom[i]==16;size=int.from_bytes(rom[i+1:i+4],'little');i+=4;out=bytearray()
 while len(out)<size:
  flags=rom[i];i+=1
  for k in range(8):
   if len(out)>=size:break
   if flags&(128>>k):
    x,y=rom[i:i+2];i+=2;offset=((x&15)<<8|y)+1
    for _ in range((x>>4)+3):out.append(out[-offset])
   else:out.append(rom[i]);i+=1
 return bytes(out[:size])
@lru_cache(None)
def tileset(t,n):
 g,p,m,_,a=words(t+4,5);return (lz(g) if raw(t,1)[0] else raw(g,n*32)),p,m
nibbles=[bytes([i&15,i>>4]) for i in range(256)]
@lru_cache(100000)
def tile_image(t0,t1,index,palette):
 a,pa,ma=tileset(t0,640);b,pb,mb=tileset(t1,384)
 data=(a if index<640 else b)[32*(index if index<640 else index-640):][:32]
 if len(data)!=32:return Image.new('RGB',(8,8)),Image.new('L',(8,8))
 indices=b''.join(nibbles[byte] for byte in data)
 image=Image.frombytes('P',(8,8),indices)
 colors=[]
 for c in halves((pa if palette<7 else pb)+32*palette,16):colors.extend(((c&31)*255//31,(c>>5&31)*255//31,(c>>10&31)*255//31))
 image.putpalette(colors+[0]*(768-len(colors)))
 return image.convert('RGB'),Image.frombytes('L',(8,8),bytes(255 if i else 0 for i in indices))
@lru_cache(100000)
def metatile(t0,t1,index):
 a,pa,ma=tileset(t0,640);b,pb,mb=tileset(t1,384)
 values=halves((ma if index<640 else mb)+16*(index if index<640 else index-640),8);image=Image.new('RGB',(16,16))
 for k,v in enumerate(values):
  tile,mask=tile_image(t0,t1,v&1023,v>>12)
  if v&1024:tile=tile.transpose(Image.Transpose.FLIP_LEFT_RIGHT);mask=mask.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
  if v&2048:tile=tile.transpose(Image.Transpose.FLIP_TOP_BOTTOM);mask=mask.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
  image.paste(tile,(k%2*8,(k%4)//2*8),mask if k>=4 else None)
 return image
# Enumerate map groups from the ROM, then follow physical links from known places.
from collections import defaultdict,Counter,deque
excluded={'1/64','10/30'}
def valid(a):return 0x8000000<=a<0xa000000
def text(a):
 out='';a&=0x1ffffff
 for _ in range(64):
  if rom[a]==255:break
  n=2 if rom[a:a+2] in chars else 1;out+=chars.get(rom[a:a+n],'');a+=n
 return out.strip()
chars={bytes.fromhex(k):v for k,v in json.loads((root/'scripts/rom-charmap.json').read_text()).items()}
allmaps={}
for group in range(64):
 gp=words(0x3526a8+group*4)[0]
 if not valid(gp):break
 for number in range(256):
  hd=words(gp+number*4)[0]
  if not valid(hd):break
  layout,events,scripts,connection=words(hd,4)
  if not valid(layout) or not valid(events):break
  width,height=words(layout,2)
  if not(0<width<=256 and 0<height<=256):break
  key=f'{group}/{number}'
  if key in excluded or group==0:continue # Legacy test/shop rooms are not public destinations.
  allmaps[key]={'hd':hd,'layout':layout,'size':[width,height],'section':raw(hd+20,1)[0],'kind':raw(hd+23,1)[0],'neighbors':set()}
for key,p in allmaps.items():
 hd=p['hd'];events=words(hd+4)[0];count=raw(events+1,1)[0];ptr=words(events+8)[0]
 if count and valid(ptr):
  for i in range(count):
   x,y,e,warp,m,g=struct.unpack('<hhBBBB',raw(ptr+i*8,8));dest=f'{g}/{m}'
   if dest in allmaps:p['neighbors'].add(dest)
 cp=words(hd+12)[0]
 if valid(cp):
  count,ptr=words(cp,2)
  if 0<count<=16 and valid(ptr):
   for i in range(count):
    direction,offset,g,m,pad=struct.unpack('<IiBBH',raw(ptr+i*12,12));dest=f'{g}/{m}'
    if direction in (1,2,3,4) and dest in allmaps:p['neighbors'].add(dest)
locations=json.loads((root/'data/locations.json').read_text());existing={p['mapId'] for p in locations}
graph={key:set(p['neighbors']) for key,p in allmaps.items()}
for key,neighbors in list(graph.items()):
 for dest in neighbors:graph[dest].add(key)
seen=set(existing);queue=deque(existing)
while queue:
 for target in graph.get(queue.popleft(),set())-seen:seen.add(target);queue.append(target)
extras=sorted((set(allmaps)&seen)-existing,key=lambda key:tuple(map(int,key.split('/'))))
layouts=json.loads((root/'data/map-layouts.json').read_text());atlas=json.loads((root/'data/atlas-locations.json').read_text())
section_cells=defaultdict(set);foreign={}
for place in locations:
 key=place['mapId'];p=allmaps[key]
 section_cells[p['section']].update(atlas.get(key,[[],''])[0]);foreign.setdefault(p['section'],place.get('foreign',''))
for index,sec in enumerate(raw(0x3f2490,660)):
 if sec!=0xc5:section_cells[sec].add(index%330)
def region(key):
 section=allmaps[key]['section']
 if section_cells[section]:return [sorted(section_cells[section]),'']
 todo={key};visited={key}
 for _ in range(8):
  todo={dest for src in todo for dest in graph[src]}-visited
  sections={allmaps[dest]['section'] for dest in todo if section_cells[allmaps[dest]['section']]}
  if len(sections)==1:return [sorted(section_cells[next(iter(sections))]),'相连地图入口参考']
  if sections or not todo:break
  visited.update(todo)
 return [[],'区域图未标出此地点']
names={}
for key,p in allmaps.items():
 sec=p['section'];ptr=words(0x3f1cac+4*(sec-0x58))[0] if sec>=0x58 else 0
 names[key]=text(ptr) if valid(ptr) else '未命名地点'
labels={1:'城镇',2:'城镇',3:'野外',4:'洞穴',5:'水下',6:'水域',8:'室内',9:'室内'}
counts=Counter();rows=[];errors=[]
for index,key in enumerate(extras):
 p=allmaps[key];base=names[key];kind=labels.get(p['kind'],'其他');counts[base,kind]+=1
 # Keep ROM names and distinguish same-name interiors without inventing building functions.
 siblings=[k for k in extras if names[k]==base and labels.get(allmaps[k]['kind'],'其他')==kind]
 suffix=f'（{kind} {counts[base,kind]}）' if len(siblings)>1 or any(q['name'].split('（')[0]==base for q in locations) else ''
 name={'3/11':'宾利市（东区）','14/0':'宾利市（红灯区）','14/2':'宾利市（白莹区）'}.get(key,base+suffix);anchor='location-'+key.replace('/','-')
 rows.append({'name':name,'mapId':key,'foreign':foreign.get(p['section'],''),'anchor':anchor,'methods':[],'pokemon':[]})
 atlas[key]=region(key)
 width,height=p['size'];layout=p['layout'];blocks,t0,t1=words(layout+12,3)
 asset=root/'locations/assets'/f'{key.replace("/","-")}.webp'
 if asset.exists():
  layouts[key]=['',width,height,[],[]];continue
 image=Image.new('RGB',(width*16,height*16))
 try:
  for y in range(height):
   for x in range(width):
    tile=halves(blocks+2*(y*width+x),1)[0]&1023
    image.paste(metatile(t0,t1,tile),(x*16,y*16))
  image.save(asset,lossless=True,method=3)
  layouts[key]=['',width,height,[],[]]
 except (ValueError,IndexError,struct.error,AssertionError) as error:errors.append((key,str(error)))
 if (index+1)%75==0:print('Rendered',index+1,'/',len(extras),flush=True)
assert not errors,errors
assert not(set(extras)&excluded)
(root/'data/atlas-extra-locations.json').write_text(json.dumps(rows,ensure_ascii=False,separators=(',',':')))
(root/'data/map-layouts.json').write_text(json.dumps(layouts,ensure_ascii=False,separators=(',',':')))
(root/'data/atlas-locations.json').write_text(json.dumps(atlas,ensure_ascii=False,separators=(',',':')))
print('Added',len(rows),'non-encounter places; all have terrain images.',flush=True)
