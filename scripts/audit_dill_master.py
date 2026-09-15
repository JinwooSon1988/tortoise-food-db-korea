#!/usr/bin/env python3
from pathlib import Path
import json, re
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'
plants=json.loads((DATA/'plants.json').read_text(encoding='utf-8'))
ass=[]
for p in [DATA/'assessments.json']+sorted(DATA.glob('assessments_korea_addendum*.json'),key=lambda x:int(re.search(r'_(\d+)\.json$',x.name).group(1)) if re.search(r'_(\d+)\.json$',x.name) else 1):
    ass.extend(json.loads(p.read_text(encoding='utf-8')))
ids={p['id'] for p in plants}; assessed={a['plant_id'] for a in ass if a.get('plant_id') in ids}
cov=json.loads((DATA/'coverage.json').read_text(encoding='utf-8'))
assert len(plants)==67, len(plants)
assert len(assessed)==64, len(assessed)
assert cov['master_review_accounting']=={'assessed':64,'identity_blocked':2,'evidence_blocked':1,'total':67}
assert 'dill' in ids and 'dill' in assessed
assert not cov.get('pending_master_candidates')
assert (ROOT/'plant/dill/index.html').exists()
text=(ROOT/'plant/dill/index.html').read_text(encoding='utf-8')
assert '제한적 보조식 근거' in text and '씨앗' in text
print('PASS dill master 67 atomic promotion')
