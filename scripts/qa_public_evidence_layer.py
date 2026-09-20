#!/usr/bin/env python3
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/"data/public_evidence_records.json").read_text(encoding="utf-8"))
required=["id","plant_ids","source_title","source_type","animal_taxon","applicability","plant_taxon","plant_part_state","directness","supports","does_not_support","url"]
allowed_directness={"direct","related_taxon","contextual","composition_only"}
allowed_applicability={"exact_taxon","species","mediterranean_testudo","tortoise_general","herbivorous_reptile_general","composition_only"}
seen=set()
errors=[]
for i,r in enumerate(data.get("records",[])):
    label=r.get("id",f"index:{i}")
    if label in seen: errors.append(f"duplicate evidence id: {label}")
    seen.add(label)
    for k in required:
        v=r.get(k)
        if v is None or v=="" or v==[]: errors.append(f"{label}: missing {k}")
    if r.get("directness") not in allowed_directness: errors.append(f"{label}: invalid directness")
    if r.get("applicability") not in allowed_applicability: errors.append(f"{label}: invalid applicability")
    if not isinstance(r.get("plant_ids"),list): errors.append(f"{label}: plant_ids must be list")
    if r.get("supports")==r.get("does_not_support"): errors.append(f"{label}: supports and limitation must differ")
if errors:
    raise SystemExit("Evidence Layer QA failed:\n- "+"\n- ".join(errors))
print(f"Evidence Layer QA passed: {len(seen)} records")
