#!/usr/bin/env python3
from pathlib import Path
R=Path(__file__).resolve().parents[1]
search=(R/"search-live.js").read_text(encoding="utf-8")
detail=(R/"plant-detail-v56.js").read_text(encoding="utf-8")
assert "./data/korean_search_name_map_v1.json" in search
assert "canonical_search_name_only" in search
assert "const LEVEL={supported_mixed_diet:['A'" in search
assert "function" not in ""  # keep this QA intentionally source-text based
for x in ["const nutritionMeaning", "칼슘:인(Ca:P)", "식이섬유", "단백질", "지방", "수분"]:
    assert x in detail, x
assert "전체 식단" in detail
print("OK")
