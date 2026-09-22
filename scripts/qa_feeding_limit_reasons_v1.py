#!/usr/bin/env python3
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
limits=json.loads((root/'data/feeding_limit_reasons_v1.json').read_text(encoding='utf-8'))
ev=json.loads((root/'data/public_evidence_records.json').read_text(encoding='utf-8'))['records']
ass=json.loads((root/'data/assessments.json').read_text(encoding='utf-8'))
eids={x['id']:x for x in ev}
med={x['plant_id'] for x in ass if x.get('species_group')=='Mediterranean_Testudo'}
errors=[]
if not med.issubset(set(limits['plants'])):
    errors.append(f"Mediterranean assessments missing classifications: {sorted(med-set(limits['plants']))}")
# Additional classified plants are allowed when another species_group has evidence-backed limits (e.g. do_not_feed).
for pid,block in limits['plants'].items():
    for item in block.get('items',[]):
        cat=item.get('category')
        if cat not in limits['categories']: errors.append(f"{pid}: unknown category {cat}")
        basis=item.get('evidence_basis')
        if basis!='assessment_existing':
            if basis not in eids: errors.append(f"{pid}: missing evidence {basis}")
            elif pid not in eids[basis].get('plant_ids',[]): errors.append(f"{pid}: evidence {basis} does not cover plant")
        if cat in {'nutritional_limitation','phytochemical_concern'} and basis=='assessment_existing':
            errors.append(f"{pid}: {cat} requires explicit evidence, not assessment_existing")
if errors:
    raise SystemExit("\n".join(errors))
print(f"OK: {len(limits['plants'])} Mediterranean plants; explicit hazard claims require linked evidence")
