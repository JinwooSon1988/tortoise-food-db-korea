#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
plants=json.loads((R/"data/plants.json").read_text(encoding="utf-8"))
d=json.loads((R/"data/korean_search_name_map_v1.json").read_text(encoding="utf-8"))
ids={p["id"] for p in plants}; rows=d["records"]; rec={x["plant_id"]:x for x in rows}
assert plants and rows
assert len(rec)==len(rows), "duplicate plant_id in Korean search-name map"
assert set(rec).issubset(ids)
assert all(x["mapping_status"] in {"canonical_search_name_only","name_candidate_only"} for x in rec.values())
assert all(x["retail_terms"] and x["master_scientific"] for x in rec.values())
candidates={p["id"] for p in plants if p.get("identity_status")=="candidate_name"}
assert not (candidates & set(rec)), "candidate intake names must not be promoted into the verified Korean search-name map"
print(f"OK: {len(rec)} verified search-name records are unique, mapped to current master plants, and separate from {len(candidates)} intake candidates")
