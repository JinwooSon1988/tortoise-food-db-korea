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
for x in ["Ca:P", "식이섬유", "칼슘", "단백질", "수분", "영양수치는 판정을 보조하는 근거이며"]:
    assert x in gen, x
# Same rules in the current (2026-10 polite-style) copy or the earlier wording.
for alts in (("검증된 수치만 표시", "검증된 성분값만 표시"),
             ("실제 섭식·수의학·독성·항영양성분 근거보다 단독으로 우선하지 않",),
             ("미확인 항목을 0으로 간주하지 않", "자료 부재를 0으로 처리하거나"),
             ("자료가 없다는 사실은 안전하거나 위험하다는 뜻이 아닙니다", "안전·위험 판정의 근거로 쓰지 않는다")):
    assert any(a in gen for a in alts), alts
print("OK")
