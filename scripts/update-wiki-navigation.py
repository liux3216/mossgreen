"""Keep catalog and walkthrough links in every shared wiki sidebar."""
from pathlib import Path
import re
root=Path(__file__).resolve().parent.parent
count=0
for path in root.rglob('*.html'):
 if '.git' in path.parts:continue
 text=path.read_text()
 def update(match):
  aside=match[0]
  if 'href="machines/"' not in aside:
   aside=re.sub(r'(<a href="moves/"[^>]*>招式一览</a>)',r'\1<a href="machines/">招式学习机</a>',aside,count=1)
  if 'href="walkthrough/"' not in aside:
   aside=re.sub(r'(<a href="locations/atlas/"[^>]*>查看地图</a>)',r'\1<a href="walkthrough/">流程攻略</a>',aside,count=1)
  return aside
 result=re.sub(r'<aside\b[^>]*class="wiki-sidebar"[\s\S]*?</aside>',update,text)
 if result!=text:path.write_text(result);count+=1
print('Updated wiki navigation in',count,'pages/templates')
