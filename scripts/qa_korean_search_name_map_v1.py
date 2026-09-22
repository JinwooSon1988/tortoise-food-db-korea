#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
plants=json.loads((R/"data/plants.json").read_text(encoding="utf-8"))
d=json.loads((R/"data/korean_search_name_map_v1.json").read_text(encoding="utf-8"))
ids={p["id"] for p in plants}; rec={x["plant_id"]:x for x in d["records"]}
assert len(plants)==69 and len(rec)==69
assert ids==set(rec)
assert all(x["mapping_status"] in {"canonical_search_name_only","name_candidate_only"} for x in rec.values())
assert all(x["retail_terms"] and x["master_scientific"] for x in rec.values())
print("OK: 69/69 published plants have a Korean search-name record; retail mappings remain separately qualified")
