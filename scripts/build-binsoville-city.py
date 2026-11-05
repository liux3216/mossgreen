"""Render the five connected Binsoville outdoor maps and verified points of interest.
Requires Pillow. Usage: python scripts/build-binsoville-city.py game.gba
"""
from pathlib import Path
import struct,json,sys,hashlib,re
from functools import lru_cache
from PIL import Image
root=Path(__file__).resolve().parent.parent
rom=Path(sys.argv[1]).read_bytes()
def raw(a,n):return rom[a&0x1ffffff:][:n]
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
@lru_cache(10000)
def metatile(t0,t1,index):
 a,pa,ma=tileset(t0,640);b,pb,mb=tileset(t1,384)
 values=halves((ma if index<640 else mb)+16*(index if index<640 else index-640),8);image=Image.new('RGB',(16,16))
 for k,v in enumerate(values):
  tile=v&1023;palette=v>>12;pal=halves((pa if palette<7 else pb)+32*palette,16)
  colors=[((c&31)*255//31,(c>>5&31)*255//31,(c>>10&31)*255//31) for c in pal]
  data=(a if tile<640 else b)[32*(tile if tile<640 else tile-640):][:32]
  if len(data)<32:continue
  for y in range(8):
   for x in range(8):
    xx=7-x if v&1024 else x;yy=7-y if v&2048 else y;c=data[yy*4+xx//2]>>(4*(xx%2))&15
    if c or k<4:image.putpixel((k%2*8+x,(k%4)//2*8+y),colors[c])
 return image
maps=[(3,10,0,75),(3,11,100,75),(14,0,0,0),(14,1,100,0),(14,2,200,75)]
canvas=Image.new('RGB',(4800,2400),'#edf3ed');warps=[];clowns=[]
for g,m,ox,oy in maps:
 hd=header(g,m);layout=words(hd)[0];w,h=words(layout,2);q,t0,t1=words(layout+12,3)
 for i,value in enumerate(halves(q,w*h)):canvas.paste(metatile(t0,t1,value&1023),(16*(ox+i%w),16*(oy+i//w)))
 ev=words(hd+4)[0];npc_count,warp_count,_,_=raw(ev,4);objects,doors=words(ev+4,2)
 for i in range(npc_count):
  a=objects+24*i
  if raw(a+1,1)[0]==100:
   x,y=halves(a+4,2);clowns.append((g,m,x+ox,y+oy))
 for i in range(warp_count):
  x,y,elev,target_warp,tm,tg=struct.unpack('<hhBBBB',raw(doors+8*i,8));warps.append((x+ox,y+oy,tg,tm,target_warp))
# Exterior door destinations and adjacent signs identify all four gym entrances.
gym_specs=[('gym-1','白莹区道馆','冯弦先生 · 钢／草',(263,101),14,3),('gym-2','红灯区道馆','宫羽先生 · 钢／水',(45,37),14,15),('gym-3','绿火区道馆','米利先生 · 钢／火',(163,58),14,16),('gym-4','宾利市道馆','宾索 · 第四个道馆',(161,119),14,17)]
pois=[]
for order,(id,name,description,(x,y),tg,tm) in enumerate(gym_specs,1):
 assert any((wx,wy,g,m)==(x,y,tg,tm) for wx,wy,g,m,_ in warps)
 pois.append({'id':id,'kind':'gym','label':str(order),'name':name,'description':description,'x':16*x+8,'y':16*y+8})
expected=[(3,10,20,100),(14,0,39,21),(14,1,141,34)];assert sorted(clowns)==sorted(expected)
for order,(_,_,x,y) in enumerate(expected,1):
 pois.append({'id':'clown-'+str(order),'kind':'clown','label':str(order),'name':['主城区小丑','红灯区小丑','绿火区小丑'][order-1],'description':['遥控器任务：第一名小丑','遥控器任务：第二名小丑','遥控器任务：第三名小丑，取回遥控器'][order-1],'x':16*x+8,'y':16*y+8})
centers=[(x,y) for x,y,g,m,_ in warps if (g,m)==(14,6)]
assert centers==[(58,81)]
for i,(x,y) in enumerate(centers,1):pois.append({'id':'center-'+str(i),'kind':'center','label':str(i),'name':'宾利市精灵中心','description':'主城区 · 精灵中心入口','x':16*x+8,'y':16*y+8})
daycare=[(x,y) for x,y,g,m,target_warp in warps if (g,m,target_warp)==(14,9,0)]
assert daycare==[(87,117)]
for i,(x,y) in enumerate(daycare,1):pois.append({'id':'daycare-'+str(i),'kind':'daycare','label':str(i),'name':'饲养屋（培育屋）','description':'从室内顶部中央后门出去，可到达分区一草地。','x':16*x+8,'y':16*y+8})
output=root/'locations/assets/binsoville-city.webp';canvas.save(output,'WEBP',lossless=True,method=6)
version=hashlib.sha256(output.read_bytes()).hexdigest()[:12]
(root/'data/binsoville-city.json').write_text(json.dumps({'width':4800,'height':2400,'image':'locations/assets/binsoville-city.webp?v='+version,'pois':pois},ensure_ascii=False,separators=(',',':')))
print('Rendered five-map city; verified 4 gyms, 3 clowns 1 Pokémon Center and 1 daycare entrance.')
