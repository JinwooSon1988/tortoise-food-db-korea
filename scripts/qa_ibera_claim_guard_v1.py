#!/usr/bin/env python3
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
evidence_rows = json.loads((ROOT / 'data/public_evidence_records.json').read_text(encoding='utf-8')).get('records', [])
evidence = {row['id']: row for row in evidence_rows}
assessment_paths = [ROOT / 'data/assessments.json'] + sorted((ROOT / 'data').glob('assessments_korea_addendum*.json'))

ibera_claim = re.compile(r'(?:Testudo graeca ibera|T\.\s*g\.\s*ibera|이베라)', re.I)
exact_ibera = re.compile(r'Testudo\s+graeca\s+ibera', re.I)
errors = []
checked = 0

for path in assessment_paths:
    if not path.exists():
        continue
    for row in json.loads(path.read_text(encoding='utf-8')):
        checked += 1
        text = ' '.join(str(row.get(k, '')) for k in ('why', 'applicability_note'))
        if not ibera_claim.search(text):
            continue
        linked = [evidence[eid] for eid in row.get('evidence_ids', []) if eid in evidence]
        supported = any(
            ev.get('applicability') == 'exact_taxon'
            and exact_ibera.search(str(ev.get('animal_taxon', '')))
            for ev in linked
        )
        if not supported:
            errors.append(f"{path.name}:{row.get('plant_id')}: Ibera-specific wording lacks exact_taxon T. g. ibera evidence")

if errors:
    raise SystemExit('Ibera claim guard failed:\n- ' + '\n- '.join(errors))
print(f'Ibera claim guard passed: {checked} assessments checked.')
