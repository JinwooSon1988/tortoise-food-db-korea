from pathlib import Path
root=Path(__file__).resolve().parents[1]
plant=root/'plant'
needle='</head>'
assets='<link rel="stylesheet" href="../../plant-detail-v56.css"><script defer src="../../plant-detail-v56.js"></script></head>'
changed=0
for page in sorted(plant.glob('*/index.html')):
    s=page.read_text(encoding='utf-8')
    if 'plant-detail-v56.js' in s: continue
    if needle not in s: raise SystemExit(f'missing head close: {page}')
    page.write_text(s.replace(needle,assets,1),encoding='utf-8')
    changed+=1
print(f'injected v5.6 detail enhancer into {changed} plant pages')
