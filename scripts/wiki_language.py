"""Include the shared language picker in static pages and generated templates."""
from hashlib import sha256
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ('wiki-language.css', 'wiki-language.js')

def add_wiki_language(page):
    if 'class="wiki-header"' not in page:
        return page
    for asset in ASSETS:
        version = sha256((ROOT / asset).read_bytes()).hexdigest()[:12]
        url = asset + '?v=' + version
        asset_pattern = re.escape(asset) + r'(?:\?v=[a-f0-9]+)?(?=")'
        if re.search(asset_pattern, page):
            page = re.sub(asset_pattern, url, page)
            continue
        if asset.endswith('.css'):
            tag = '<link rel="stylesheet" href="' + url + '">'
        else:
            tag = '<script src="' + url + '" defer></script>'
        # The page base is already declared by the first script or end of head.
        first_script = page.find('<script src=')
        start = first_script if first_script != -1 else page.index('</head>')
        page = page[:start] + tag + '\n' + page[start:]
    return page

if __name__ == '__main__':
    count = 0
    for path in ROOT.rglob('*.html'):
        if '.git' in path.parts:
            continue
        old = path.read_text()
        new = add_wiki_language(old)
        if new != old:
            path.write_text(new)
            count += 1
    print('Updated language picker in', count, 'pages and templates')
