"""Post-generation guard for plant detail pages.

Verdicts, identity notes and direct Ibera observations are rendered statically by
scripts/generate_static_pages.py from data/public_assessments.json. The retired
runtime enhancers (plant-detail-v56.js, ibera-direct-evidence-v56.js) re-derived
verdicts from legacy assessment files and a species selector, so this step strips
any reference to them instead of injecting them.
"""
from pathlib import Path
import re

root=Path(__file__).resolve().parents[1]
RETIRED=re.compile(r'<link rel="stylesheet" href="\.\./\.\./plant-detail-v56\.css">|<script defer src="\.\./\.\./(?:plant-detail-v56|ibera-direct-evidence-v56)\.js"></script>')
changed=0
for page in sorted((root/'plant').glob('*/index.html')):
    s=page.read_text(encoding='utf-8')
    t=RETIRED.sub('',s)
    if t!=s:
        page.write_text(t,encoding='utf-8')
        changed+=1
print(f'plant detail guard: removed retired runtime enhancers from {changed} pages')
