#!/usr/bin/env python3
from pathlib import Path
import json, re
ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/'data'
plants=json.loads((DATA/'plants.json').read_text(encoding='utf-8')); ids={p['id'] for p in plants}
ass=[]
for p in [DATA/'assessments.json']+sorted(DATA.glob('assessments_korea_addendum*.json'),key=lambda x:int(re.search(r'_(\d+)\.json$',x.name).group(1)) if re.search(r'_(\d+)\.json$',x.name) else 1):
    ass.extend(json.loads(p.read_text(encoding='utf-8')))
assessed={a['plant_id'] for a in ass if a.get('plant_id') in ids}; cov=json.loads((DATA/'coverage.json').read_text(encoding='utf-8'))
assert len(plants)>=68, len(plants)
assert len(assessed)>=65, len(assessed)
acct=cov.get('master_review_accounting') or {}
assert acct.get('total')==len(plants), (acct,len(plants))
assert acct.get('assessed')==len(assessed), (acct,len(assessed))
assert 'chard' in ids and 'chard' in assessed and 'chard' not in (cov.get('pending_master_candidates') or [])
rows=[a for a in ass if a.get('plant_id')=='chard']; assert len(rows)==1
row=rows[0]; assert row['species_group']=='Tortoise_general' and row['verdict']=='limited_supplement' and row['confidence']=='C'
assert (ROOT/'plant/chard/index.html').exists(); text=(ROOT/'plant/chard/index.html').read_text(encoding='utf-8')
assert '제한적 보조식 근거' in text and '옥살산' in text and 'Mediterranean Testudo' in text
assert 'plant/chard/' in (ROOT/'sitemap.xml').read_text(encoding='utf-8')
print('PASS chard regression gate; master',len(plants),'assessed',len(assessed))
