from pathlib import Path
import json
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parents[1]
origin = 'https://jinwooson1988.github.io/tortoise-food-db-korea/'
robots = (root / 'robots.txt').read_text(encoding='utf-8')
index = (root / 'index.html').read_text(encoding='utf-8')
plants = json.loads((root / 'data' / 'plants.json').read_text(encoding='utf-8'))

assert 'User-agent: *' in robots
assert 'Allow: /' in robots
assert f'Sitemap: {origin}sitemap.xml' in robots
assert f'<link rel="canonical" href="{origin}">' in index
assert '<meta name="description"' in index

xml_root = ET.parse(root / 'sitemap.xml').getroot()
ns = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
urls = [n.text for n in xml_root.findall('s:url/s:loc', ns)]
assert len(urls) == len(set(urls)), 'duplicate sitemap URLs'
assert origin in urls
for p in plants:
    url = f'{origin}plant/{p["id"]}/'
    assert url in urls, p['id']
    assert (root / 'plant' / p['id'] / 'index.html').exists(), p['id']
for path in ('today','meal','weekly','growth','monthly','trends','profile','settings'):
    assert f'{origin}{path}/' in urls, path
    assert (root / path / 'index.html').exists(), path

print(f'public discovery audit: PASS ({len(plants)} plants, {len(urls)} sitemap URLs)')
