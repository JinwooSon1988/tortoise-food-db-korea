#!/usr/bin/env python3
from pathlib import Path
import json, sys
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'
plants=json.loads((DATA/'plants.json').read_text(encoding='utf-8'))
sys.path.insert(0,str(ROOT/'scripts'))
from public_verdict import load_assessments
# Canonical registry is data/public_assessments.json (legacy assessments*.json files are no longer the publication source).
ass=load_assessments()
ids={p['id'] for p in plants}
cov=json.loads((DATA/'coverage.json').read_text(encoding='utf-8'))
blocked=set(cov.get('identity_blocked_priority') or [])|set(cov.get('evidence_blocked_priority') or [])
assessed={a['plant_id'] for a in ass if a.get('plant_id') in ids}-blocked
# Regression gate: the catalog may grow beyond 67/64, but dill must never regress.
assert len(plants)>=67, len(plants)
assert len(assessed)>=64, len(assessed)
# Dill-specific regression gate only. Global master accounting is maintained separately
# because the catalog now contains explicit intake candidates not yet eligible for publication.
assert 'dill' in ids and 'dill' in assessed
assert 'dill' not in (cov.get('pending_master_candidates') or [])
assert (ROOT/'plant/dill/index.html').exists()
text=(ROOT/'plant/dill/index.html').read_text(encoding='utf-8')
# Page copy was reworded in the Korean copy pass; the seed exclusion must still be stated explicitly.
assert 'C · 가끔 보조 급여' in text and '씨앗은 먹이지 않고' in text and '씨앗은 명시적으로 제외' in text
print('PASS dill regression gate; master',len(plants),'assessed',len(assessed))
