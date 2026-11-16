"""Restore map assets that were previously reduced to 960 pixels.

Usage: python3 scripts/render-map-assets.py game.gba [--cemetery-water-only]
Requires Pillow. Export directly from ROM, never enlarge an existing thumbnail.
"""
from pathlib import Path
import argparse,hashlib,json
from PIL import Image
from rom_map_renderer import load_rom,render_layout,render_map,halves,words

root=Path(__file__).resolve().parent.parent
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('rom',type=Path)
parser.add_argument('--cemetery-water-only',action='store_true')
args=parser.parse_args()
load_rom(args.rom.read_bytes())

def render_cemetery_water():
 # The cemetery's on-load script can switch to layout 279.
 if halves(0x081630aa,1)!=(279,):
  return False
 layout=0x0833be30
 width,height=words(layout,2)
 blocks,primary,secondary=words(layout+12,3)
 primary_attrs,secondary_attrs=(words(tileset+20)[0] for tileset in (primary,secondary))
 block_words=halves(blocks,width*height)

 def attributes(block):
  tile=block&0x03ff
  address=primary_attrs+4*tile if tile<640 else secondary_attrs+4*(tile-640)
  return words(address)[0]

 # Older ROMs have the original mismatched graphics and no dry ladder platforms.
 for x,y in [(3,9),(32,16)]:
  block=block_words[y*width+x]
  if block>>10!=12 or attributes(block)&0x01ff!=0x61:
   return False

 land,water=[],[]
 for index,block in enumerate(block_words):
  if block&0x0c00:
   continue
  encounter_type=(attributes(block)>>24)&7
  if encounter_type==1:
   land.append(index)
  elif encounter_type==2:
   water.append(index)

 relative_asset='locations/assets/1-87-water.webp'
 asset=root/relative_asset
 render_layout(layout).save(asset,lossless=True,method=6)
 version=hashlib.sha256(asset.read_bytes()).hexdigest()[:12]
 map_data=[relative_asset+'?v='+version,width,height,land,water]
 (root/'data/cemetery-water-layout.json').write_text(json.dumps(map_data,separators=(',',':'))+'\n')
 print('Rendered the cemetery water layout and encounter grid.')
 return True

water_rendered=render_cemetery_water()
if args.cemetery_water_only:
 if not water_rendered:
  parser.error('Use the cemetery water repair ROM to render its updated layout.')
 raise SystemExit(0)

layouts=json.loads((root/'data/map-layouts.json').read_text())
atlas=json.loads((root/'data/atlas.json').read_text())
updated={}
for key,layout in layouts.items():
 asset=root/'locations/assets'/(key.replace('/','-')+'.webp')
 native=(layout[1]*16,layout[2]*16)
 before=None
 if asset.exists():
  with Image.open(asset) as image:before=image.size
 if before==native:continue
 image=render_map(*map(int,key.split('/')))
 assert image.size==native,(key,image.size,native)
 image.save(asset,lossless=True,method=6)
 version=hashlib.sha256(asset.read_bytes()).hexdigest()[:12]
 layout[0]='locations/assets/'+asset.name+'?v='+version
 updated[key]={'before':before,'after':native,'image':layout[0]}
 print(key,before,'→',native,flush=True)
for place in atlas:
 if place['mapId'] in updated:place['image']=updated[place['mapId']]['image']
(root/'data/map-layouts.json').write_text(json.dumps(layouts,ensure_ascii=False,separators=(',',':')))
(root/'data/atlas.json').write_text(json.dumps(atlas,ensure_ascii=False,separators=(',',':')))
print('Restored',len(updated),'maps at native pixel resolution.')
