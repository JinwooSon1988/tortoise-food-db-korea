#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
plants=json.loads((R/"data/plants.json").read_text()) 
nut=json.loads((R/"data/plant_nutrition_v56.json").read_text())
q=json.loads((R/"data/nutrition_coverage_queue_v1.json").read_text())
existing={x["plant_id"] for x in nut["plants"]}
queued={x["plant_id"] for x in q["records"]}
assert queued=={p["id"] for p in plants if p["id"] not in existing}
assert all(x["do_not_infer"] for x in q["records"])
assert all(x["mapping_status"] in {"pending_source_file","identity_scope_hold"} for x in q["records"])
print("OK")
