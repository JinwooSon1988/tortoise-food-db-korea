import json
from pathlib import Path
from urllib.parse import urlparse, parse_qs

root = Path(__file__).resolve().parents[1]
manifest = json.loads((root / 'data' / 'blog_search_links_v1.json').read_text(encoding='utf-8'))
plants = {p['id']: p for p in json.loads((root / 'data' / 'plants.json').read_text(encoding='utf-8'))}

assert manifest['base_url'] == 'https://jinwooson1988.github.io/tortoise-food-db-korea/'
assert len(manifest['links']) >= 9
seen = set()
for row in manifest['links']:
    pid = row['plant_id']
    assert pid in plants, pid
    assert pid not in seen, pid
    seen.add(pid)
    parsed = urlparse(row['search_url'])
    assert parsed.scheme == 'https'
    assert parsed.netloc == 'jinwooson1988.github.io'
    assert parsed.path == '/tortoise-food-db-korea/'
    q = parse_qs(parsed.query).get('q', [])
    assert len(q) == 1 and q[0].strip(), row
    canonical = f'https://jinwooson1988.github.io/tortoise-food-db-korea/plant/{pid}/'
    assert row['canonical_url'] == canonical
    assert (root / 'plant' / pid / 'index.html').exists(), pid

mallow = next(x for x in manifest['links'] if x['plant_id'] == 'mallow')
assert '판정 보류' in mallow['anchor']
print('blog search links audit: PASS')
