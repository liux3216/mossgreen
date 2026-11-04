"""Generate static detail routes for GitHub Pages from the shared detail template."""
import html
import json
from pathlib import Path

root = Path(__file__).resolve().parent.parent
pokemon = json.loads((root / 'data/pokemon.json').read_text())
template = (root / 'pokemon.html').read_text()
for identifier, record in pokemon.items():
    page = template.replace('<head>', '<head>\n<base href="../../">', 1)
    page = page.replace('<body>', '<body data-pokemon-id="' + identifier + '">', 1)
    page = page.replace('<title>宝可梦资料 · 青苔 Wiki</title>',
                        '<title>' + html.escape(record['name']) + ' · 青苔 Wiki</title>', 1)
    destination = root / 'pokemons' / identifier
    destination.mkdir(parents=True, exist_ok=True)
    (destination / 'index.html').write_text(page)
print('Generated', len(pokemon), 'Pokemon detail routes')
