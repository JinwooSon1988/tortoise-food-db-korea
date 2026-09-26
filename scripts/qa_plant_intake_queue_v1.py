#!/usr/bin/env python3
import json
from pathlib import Path
r=Path(__file__).resolve().parents[1]
q=json.loads((r/'data/plant_intake_queue_v1.json').read_text(encoding='utf-8'))
p=json.loads((r/'data/plants.json').read_text(encoding='utf-8'))
master={x['id']:x for x in p}
errors=[]; seen=set()
for x in q['candidates']:
    i=x['id']
    if i in seen: errors.append(f"duplicate candidate: {i}")
    seen.add(i)
    if i in master:
        m=master[i]
        if m.get('suitability_status')!='unreviewed' or m.get('identity_status')!='candidate_name': errors.append(f"{i}: intake candidate promoted in master without review state")
    if x.get('feeding_verdict') is not None and x.get('status') not in {'assessment_ready'}:
        errors.append(f"{i}: verdict before assessment_ready")
    if x.get('status') not in q['statuses']: errors.append(f"{i}: invalid status")
    if not x.get('canonical_taxon_candidate'): errors.append(f"{i}: missing taxon candidate")
if errors: raise SystemExit("\n".join(errors))
print(f"OK: {len(seen)} intake candidates may coexist in master only as candidate_name/unreviewed; no premature verdicts")
