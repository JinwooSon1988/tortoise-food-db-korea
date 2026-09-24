#!/usr/bin/env python3
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
evrows=json.loads((ROOT/"data/public_evidence_records.json").read_text(encoding="utf-8")).get("records",[])
ev={x["id"]:x for x in evrows}
paths=[ROOT/"data/assessments.json"]+sorted((ROOT/"data").glob("assessments_korea_addendum*.json"))
allowed={
 "tortoise_general":{"exact_taxon","species","mediterranean_testudo","tortoise_general"},
 "herbivorous_reptile_general":{"exact_taxon","species","mediterranean_testudo","tortoise_general","herbivorous_reptile_general"},
}
errors=[];checked=0
for path in paths:
  if not path.exists(): continue
  for row in json.loads(path.read_text(encoding="utf-8")):
    scope=row.get("assessment_scope")
    if scope not in allowed: continue
    checked+=1
    linked=[ev[e] for e in row.get("evidence_ids",[]) if e in ev]
    if not linked: continue
    if not any(x.get("applicability") in allowed[scope] and x.get("directness")!="composition_only" for x in linked):
      errors.append(f"{path.name}:{row.get('plant_id')}|{scope}: no feeding/husbandry evidence at or within declared scope")
if errors:
  raise SystemExit("General scope guard failed:\n- "+"\n- ".join(errors))
print(f"General scope guard passed: {checked} general-scope assessments checked.")
