"""Generate static detail routes for GitHub Pages from the shared detail template."""
import html
import hashlib
import json
import re
from pathlib import Path

root = Path(__file__).resolve().parent.parent
pokemon = json.loads((root / 'data/pokemon.json').read_text())
template = (root / 'pokemon.html').read_text()
# Change resource URLs whenever content changes, including for returning visitors.
for asset in ('pokemon.js', 'pokemon.css', 'pokemons/list.css'):
    digest = hashlib.sha256((root / asset).read_bytes()).hexdigest()[:12]
    template = re.sub(r'(["\'])' + re.escape(asset) + r'(?:\?[^"\']*)?(["\'])',
                      lambda match: match[1] + asset + '?v=' + digest + match[2], template)
(root / 'pokemon.html').write_text(template)
for identifier, record in pokemon.items():
    page = template.replace('<head>', '<head>\n<base href="../../">', 1)
    page = re.sub(r'<body\b([^>]*)>', lambda match: '<body' + match[1] + ' data-pokemon-id="' + identifier + '">', page, count=1)
    page = page.replace('<title>宝可梦资料 · 青苔 Wiki</title>',
                        '<title>' + html.escape(record['name']) + ' · 青苔 Wiki</title>', 1)
    destination = root / 'pokemons' / identifier
    destination.mkdir(parents=True, exist_ok=True)
    (destination / 'index.html').write_text(page)
print('Generated', len(pokemon), 'Pokemon detail routes')
