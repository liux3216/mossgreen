"""Restore map assets that were previously reduced to 960 pixels.

Usage: python3 scripts/render-map-assets.py game.gba
Requires Pillow. Export directly from ROM, never enlarge an existing thumbnail.
"""
from pathlib import Path
import hashlib,json,sys
from PIL import Image
from rom_map_renderer import load_rom,render_map

root=Path(__file__).resolve().parent.parent
load_rom(Path(sys.argv[1]).read_bytes())
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
