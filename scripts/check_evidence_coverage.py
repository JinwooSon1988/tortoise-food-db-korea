#!/usr/bin/env python3
"""Fail CI if catalog coverage counters do not agree; report progress toward 90%."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
idx=json.loads((root/"data/plant-catalog/index.json").read_text(encoding="utf-8"))
total=linked=checked=0
for shard in idx["shards"]:
    records=json.loads((root/"data/plant-catalog"/shard["file"]).read_text(encoding="utf-8"))["records"]
    total+=len(records)
    for r in records:
        evidence=r.get("feeding_evidence") or []
        linked+=bool(evidence)
        checked+=any(e.get("verification") in ("full_text_verified","review_full_text_verified","guideline_full_text_verified") for e in evidence)
assert total==idx["count"],(total,idx["count"])
assert linked==idx["counts"]["with_feeding_evidence"],(linked,idx["counts"]["with_feeding_evidence"])
target=(total*9+9)//10
result={"total_species":total,"linked_species":linked,"source_checked_species":checked,
        "coverage_percent":round(100*linked/total,2),"target_90_percent":target,
        "remaining_to_target":max(0,target-linked),
        "note":"Evidence presence is not a safe-to-feed grade. Development branch only."}
print(json.dumps(result,ensure_ascii=False,indent=2))
