from pathlib import Path
import json, sys
ROOT=Path(__file__).resolve().parents[1]
rows=json.loads((ROOT/"data/near_complete_nutrition_candidates.json").read_text(encoding="utf-8"))
errors=[]
for i,r in enumerate(rows):
    if r["state"]=="accepted":
        for k in ("record_id","source_url","food_description","preparation","basis","reviewer_note"):
            if not r.get(k): errors.append(f"{i}:{r['plant_id']} missing {k}")
        for k in ("water","protein","fiber","calcium","phosphorus"):
            if r["nutrients"].get(k) is None: errors.append(f"{i}:{r['plant_id']} missing nutrient {k}")
    if r["state"] in ("accepted","rejected") and not r.get("reviewer_note"):
        errors.append(f"{i}:{r['plant_id']} terminal state missing reviewer_note")
print("PASS" if not errors else "\n".join(errors))
sys.exit(0 if not errors else 1)
