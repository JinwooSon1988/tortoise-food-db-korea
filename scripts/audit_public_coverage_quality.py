#!/usr/bin/env python3
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
plants=json.loads((ROOT/"data/plants.json").read_text(encoding="utf-8"))
images=json.loads((ROOT/"data/verified_plant_images_v56.json").read_text(encoding="utf-8")).get("images",[])
nutrition=json.loads((ROOT/"data/plant_nutrition_v56.json").read_text(encoding="utf-8")).get("plants",[])
evidence=json.loads((ROOT/"data/public_evidence_records.json").read_text(encoding="utf-8")).get("records",[])
ids=[p["id"] for p in plants]
image_ids={x["plant_id"] for x in images}
nutrition_ids={x["plant_id"] for x in nutrition}
evidence_count={}
for r in evidence:
    for pid in r.get("plant_ids",[]): evidence_count[pid]=evidence_count.get(pid,0)+1
missing_images=[x for x in ids if x not in image_ids]
missing_nutrition=[x for x in ids if x not in nutrition_ids]
no_evidence=[x for x in ids if not evidence_count.get(x)]
print(f"plants: {len(ids)}")
print(f"verified images: {len(image_ids)}/{len(ids)}")
print(f"verified nutrition: {len(nutrition_ids)}/{len(ids)}")
print(f"public evidence records: {len(evidence)}")
print("missing images:", ", ".join(missing_images) or "none")
print("missing nutrition:", ", ".join(missing_nutrition) or "none")
print("no public evidence:", ", ".join(no_evidence) or "none")
# This is a coverage audit, not a pass/fail safety gate. Missing data stays explicit.
