#!/usr/bin/env python3
from pathlib import Path
R=Path(__file__).resolve().parents[1]
search=(R/"search-live.js").read_text(encoding="utf-8")
gen=(R/"scripts/generate_static_pages.py").read_text(encoding="utf-8")
assert "./data/korean_search_name_map_v1.json" in search
assert "canonical_search_name_only" in search
# search-live.js only suggests names; it must not carry its own verdict table or legacy assessment data.
assert "const LEVEL=" not in search and "assessments.json" not in search
# Nutrition on detail pages is context only and never changes the grade.
for x in ["Ca:P", "식이섬유", "칼슘", "단백질", "수분", "검증된 성분값만 표시한다", "영양수치는 판정을 보조하는 근거이며", "실제 섭식·수의학·독성·항영양성분 근거보다 단독으로 우선하지 않는다", "자료 부재를 0으로 처리하거나"]:
    assert x in gen, x
print("OK")
