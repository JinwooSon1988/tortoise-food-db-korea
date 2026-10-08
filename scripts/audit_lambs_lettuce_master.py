#!/usr/bin/env python3
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/'data'
sys.path.insert(0,str(ROOT/'scripts'))
from public_verdict import load_assessments, display
plants=json.loads((DATA/'plants.json').read_text(encoding='utf-8')); ids={p['id'] for p in plants}
# Canonical registry is data/public_assessments.json (legacy assessments*.json files are no longer the publication source).
ass=load_assessments(); cov=json.loads((DATA/'coverage.json').read_text(encoding='utf-8'))
blocked=set(cov.get('identity_blocked_priority') or [])|set(cov.get('evidence_blocked_priority') or [])
assessed={a['plant_id'] for a in ass if a.get('plant_id') in ids}-blocked
assert len(plants)>=69, len(plants); assert len(assessed)>=66, len(assessed)
acct=cov.get('master_review_accounting') or {}
assert acct.get('total')==len(plants), (acct,len(plants))
assert acct.get('assessed')==len(assessed), (acct,len(assessed))
rows=[a for a in ass if a.get('plant_id')=='lambs_lettuce']; assert len(rows)==1
row=rows[0]; assert row['species_group']=='Tortoise_general' and row['verdict']=='supplement_general_evidence' and row['confidence']=='C'
assert (ROOT/'plant/lambs_lettuce/index.html').exists(); text=(ROOT/'plant/lambs_lettuce/index.html').read_text(encoding='utf-8')
g=display(row)
# Current page copy: canonical grade label and evidence scoped to general tortoises (not Mediterranean Testudo).
assert f"{g['grade']} · {g['label']}" in text and '연구·자료 대상</dt><dd>육지거북 일반' in text
assert '지중해 Testudo 근거' not in text
assert 'plant/lambs_lettuce/' in (ROOT/'sitemap.xml').read_text(encoding='utf-8')
print('PASS Lambs Lettuce regression gate; master',len(plants),'assessed',len(assessed))
