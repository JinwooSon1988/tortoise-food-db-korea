import json
import re
from pathlib import Path

root = Path(__file__).resolve().parents[1]
base = 'https://jinwooson1988.github.io/tortoise-food-db-korea/'
plants = json.loads((root/'data/plants.json').read_text(encoding='utf-8'))

def read(path): return path.read_text(encoding='utf-8')
def meta(html, name):
    m = re.search(r'<meta name=["\']'+re.escape(name)+r'["\'] content=["\']([^"\']+)', html, re.I)
    return m.group(1).strip() if m else ''
def title(html):
    m = re.search(r'<title>(.*?)</title>', html, re.I|re.S)
    return re.sub(r'\s+',' ',m.group(1)).strip() if m else ''
def canonical(html):
    m = re.search(r'<link rel=["\']canonical["\'] href=["\']([^"\']+)', html, re.I)
    return m.group(1).strip() if m else ''

home = read(root/'index.html')
assert 10 <= len(title(home)) <= 60
assert 30 <= len(meta(home,'description')) <= 160
assert canonical(home) == base

for p in plants:
    pid = p['id']; path = root/'plant'/pid/'index.html'
    assert path.exists(), pid
    html = read(path)
    t = title(html); d = meta(html,'description'); c = canonical(html)
    assert p.get('ko', pid) in t, (pid,t)
    assert '육지거북' in t, (pid,t)
    assert 10 <= len(t) <= 70, (pid,len(t))
    assert 20 <= len(d) <= 180, (pid,len(d))
    assert c == base+f'plant/{pid}/', (pid,c)
    blocks = re.findall(r'<script type=["\']application/ld\+json["\']>(.*?)</script>', html, re.I|re.S)
    assert blocks, pid
    for block in blocks: json.loads(block)

print(f'search snippet audit: PASS ({len(plants)} plant pages + home)')
