from pathlib import Path
root=Path(__file__).resolve().parents[1]
plant=root/'plant'
needle='</head>'
assets='<link rel="stylesheet" href="../../plant-detail-v56.css"><script defer src="../../plant-detail-v56.js"></script><script defer src="../../ibera-direct-evidence-v56.js"></script></head>'
changed=0
for page in sorted(plant.glob('*/index.html')):
    s=page.read_text(encoding='utf-8')
    if 'ibera-direct-evidence-v56.js' in s:
        continue
    if 'plant-detail-v56.js' in s:
        s=s.replace('<script defer src="../../plant-detail-v56.js"></script>','<script defer src="../../plant-detail-v56.js"></script><script defer src="../../ibera-direct-evidence-v56.js"></script>',1)
    else:
        if needle not in s: raise SystemExit(f'missing head close: {page}')
        s=s.replace(needle,assets,1)
    page.write_text(s,encoding='utf-8')
    changed+=1
print(f'injected direct Ibera evidence enhancer into {changed} plant pages')
