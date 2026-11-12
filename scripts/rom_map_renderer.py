"""Render native 16-pixel GBA map metatiles without resizing."""
import struct
from functools import lru_cache
from PIL import Image
rom=b''
def load_rom(payload):
 global rom
 rom=payload
 tileset.cache_clear();tile_image.cache_clear();metatile.cache_clear()
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

def render_map(group,number):
 hd=header(group,number);layout=words(hd)[0]
 width,height=words(layout,2);assert 0<width<=256 and 0<height<=256
 blocks,t0,t1=words(layout+12,3)
 image=Image.new('RGB',(width*16,height*16))
 for y in range(height):
  for x in range(width):
   tile=halves(blocks+2*(y*width+x),1)[0]&1023
   image.paste(metatile(t0,t1,tile),(x*16,y*16))
 return image
