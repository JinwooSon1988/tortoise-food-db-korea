import json,sys
from pathlib import Path
d=Path(__file__).resolve().parents[1]/"data"
cand=json.loads((d/"usda_verified_candidates.json").read_text(encoding="utf-8"))
plants={p["id"] for p in json.loads((d/"plants.json").read_text(encoding="utf-8"))}
errs=[]
for c in cand:
    if c["plant_id"] not in plants: errs.append("unknown "+c["plant_id"])
    if c["status"]!="official_dataset_candidate": errs.append("bad status")
# Critical: candidates must not silently become official nutrient records.
nut=json.loads((d/"nutrition_records.json").read_text(encoding="utf-8"))
for c in cand:
    for n in nut:
        if n["plant_id"]==c["plant_id"] and n.get("source_tier")=="official_direct" and not n.get("source_record_id"):
            errs.append("unverified promotion "+c["plant_id"])
print("PASS" if not errs else "\n".join(errs));sys.exit(bool(errs))
