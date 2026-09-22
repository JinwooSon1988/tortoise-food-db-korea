#!/usr/bin/env python3
import json,re
from pathlib import Path
R=Path(__file__).resolve().parents[1]
d=json.loads((R/"data/korean_search_name_map_v1.json").read_text(encoding="utf-8"))
js=(R/"search-live.js").read_text(encoding="utf-8")
assert len(d["records"])==69 and len({x["plant_id"] for x in d["records"]})==69
assert "./data/korean_search_name_map_v1.json" in js
assert "korean_retail_name_map.json" in js
assert "mapping_status" in js
assert "name_candidate_only" in js and "canonical_search_name_only" in js
print("OK: canonical Korean search index is primary; legacy retail map is fallback only")
