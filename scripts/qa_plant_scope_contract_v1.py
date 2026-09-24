#!/usr/bin/env python3
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
rows=json.loads((ROOT/"data/public_evidence_records.json").read_text(encoding="utf-8")).get("records",[])
errors=[]
allowed={"direct","related_taxon","contextual","composition_only"}
for r in rows:
    rid=r.get("id","<missing-id>")
    for field in ("plant_taxon","plant_part_state"):
        v=r.get(field)
        if not isinstance(v,str) or not v.strip():
            errors.append(f"{rid}: missing/empty {field}")
    if r.get("directness") not in allowed:
        errors.append(f"{rid}: invalid directness {r.get('directness')}")
    if r.get("directness")=="composition_only" and not str(r.get("plant_taxon","")).strip():
        errors.append(f"{rid}: composition evidence lacks plant taxon identity")
    if not isinstance(r.get("plant_ids"),list) or not r.get("plant_ids"):
        errors.append(f"{rid}: plant_ids must be non-empty")
if errors:
    raise SystemExit("Plant evidence scope contract failed:\n- "+"\n- ".join(errors))
print(f"Plant evidence scope contract passed: {len(rows)} evidence records checked.")
