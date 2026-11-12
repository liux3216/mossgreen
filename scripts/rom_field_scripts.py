"""Map-attached FRLG script reader for this ROM, including shared subroutines."""
import json,struct
from collections import defaultdict

class FieldScripts:
 def __init__(self,rom,root):
  self.rom=rom;self.root=root;self.nodes={};self.maps={};self.roots=defaultdict(list);self.unknown={}
  commands=json.loads((root/'scripts/field-script-opcodes.json').read_text())
  self.widths={int(k):v for k,v in commands['lengths'].items()}
  self.chars={bytes.fromhex(k):v for k,v in json.loads((root/'scripts/rom-charmap.json').read_text()).items()}
  for group in range(64):
   gp=self.word(0x3526a8+group*4)
   if not self.valid(gp):break
   for number in range(256):
    hd=self.word(gp+number*4)
    if not self.valid(hd):break
    layout,events,scripts,_=self.unpack('<4I',hd)
    if not self.valid(layout) or not self.valid(events):break
    width,height=self.unpack('<II',layout)
    if not(0<width<=256 and 0<height<=256):break
    key=f'{group}/{number}';self.maps[key]={'header':hd,'size':[width,height]}
    counts=self.unpack('<4B',events)
    objects=self.word(events+4)
    if self.valid(objects):
     for i in range(counts[0]):
      p=objects+24*i;x,y=self.unpack('<hh',p+4)
      self.attach(self.word(p+16),key,'npc',localId=self.byte(p),x=x,y=y,flag=self.half(p+20))
    coords=self.word(events+12)
    if self.valid(coords):
     for i in range(counts[2]):
      p=coords+16*i;x,y=self.unpack('<hh',p)
      self.attach(self.word(p+12),key,'coordinate',x=x,y=y,variable=self.half(p+6),value=self.half(p+8))
    background=self.word(events+16)
    if self.valid(background):
     for i in range(counts[3]):
      p=background+12*i
      if self.byte(p+5)<=4:self.attach(self.word(p+8),key,'background',x=self.half(p),y=self.half(p+2))
    if self.valid(scripts):
     for i in range(50):
      kind=self.byte(scripts+5*i)
      if not kind:break
      p=self.word(scripts+5*i+1)
      if not self.valid(p):continue
      if kind in (2,4):
       for j in range(128):
        if not self.half(p+j*8):break
        self.attach(self.word(p+j*8+4),key,'map-condition',variable=self.half(p+j*8),value=self.half(p+j*8+2))
      else:self.attach(p,key,'map-script')
 def valid(self,a):return 0x08000000<=a<0x08000000+len(self.rom)
 def unpack(self,fmt,a):return struct.unpack_from(fmt,self.rom,a&0x1ffffff)
 def word(self,a):return self.unpack('<I',a)[0]
 def half(self,a):return self.unpack('<H',a)[0]
 def byte(self,a):return self.rom[a&0x1ffffff]
 def text(self,a,limit=500):
  if not self.valid(a):return ''
  i=a&0x1ffffff;out=''
  for _ in range(limit):
   if self.rom[i]==255:break
   if self.rom[i] in (0xfe,0xfa,0xfb):out+='\n';i+=1;continue
   if self.rom[i]==0xfd:out+='{VAR}';i+=2;continue
   n=2 if self.rom[i:i+2] in self.chars else 1
   out+=self.chars.get(self.rom[i:i+n],'�');i+=n
  return out.strip()
 def attach(self,a,map_id,kind,**kw):
  if self.valid(a):self.roots[a].append({'mapId':map_id,'kind':kind,**kw})
 def node(self,pc):
  if pc in self.nodes:return self.nodes[pc]
  op=self.byte(pc);n=self.widths.get(op);extra=[]
  if op==0x5c:
   mode=self.byte(pc+1);n={0:14,1:18,2:18,3:10,4:18,5:14,6:22,7:18,8:22,9:14}.get(mode)
   if mode in (1,2,6,8) and n:extra.append(self.word(pc+n-4))
  if not n:
   self.unknown[pc]=op;node={'op':op,'size':0,'next':[]}
  else:
   nxt=pc+n
   if op in (2,3,0x0d,0x24):targets=[]
   elif op==5:targets=[self.word(pc+1)]
   elif op in (4,6,7):targets=[self.word(pc+(1 if op==4 else 2)),nxt]
   elif op in (8,9,10,11):
    idx=self.byte(pc+(1 if op in (8,9) else 2))
    targets=([self.word(0x8160450+4*idx)] if idx<10 else [])+([nxt] if op!=8 else [])
   else:targets=[nxt]
   node={'op':op,'size':n,'next':[p for p in targets+extra if self.valid(p)]}
  self.nodes[pc]=node;return node
 def walk(self,start):
  todo=[start];seen=set()
  while todo:
   pc=todo.pop()
   if pc in seen:continue
   seen.add(pc);todo.extend(self.node(pc)['next'])
  return seen
