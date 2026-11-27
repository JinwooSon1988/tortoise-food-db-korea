#!/usr/bin/env python3
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
records=json.loads((ROOT/"data/public_evidence_records.json").read_text(encoding="utf-8")).get("records",[])
errors=[];warnings=[]
vague_taxon=re.compile(r"^(?:see linked plant concept|plant material|mixed plants?)",re.I)
broad_part=re.compile(r"^(?:as described by the source|plant; exact part not specified|wild plant material)",re.I)
for r in records:
    rid=r["id"]; tax=str(r.get("plant_taxon","")).strip(); part=str(r.get("plant_part_state","")).strip()
    if vague_taxon.search(tax) and r.get("directness")=="direct":
        errors.append(f"{rid}: direct evidence has non-specific plant_taxon")
    if broad_part.search(part) and r.get("directness")=="direct":
        warnings.append(f"{rid}: direct evidence retains broad/unspecified plant_part_state")
    if re.search(r"\bspp\.?\b|/|\band\b",tax,re.I) and len(r.get("plant_ids",[]))==1:
        warnings.append(f"{rid}: broad/multiple plant_taxon linked to one plant_id; do not promote to species identity")
print(f"Evidence promotion audit: {len(records)} records; {len(warnings)} conservative-scope warnings.")
for w in warnings: print("WARNING:",w)
if errors: raise SystemExit("Evidence promotion guard failed:\n- "+"\n- ".join(errors))
