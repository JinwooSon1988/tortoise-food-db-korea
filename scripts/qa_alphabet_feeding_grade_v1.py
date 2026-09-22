#!/usr/bin/env python3
from pathlib import Path
R=Path(__file__).resolve().parents[1]
js=(R/"public-plant-card-v56.js").read_text(encoding="utf-8")
allp=(R/"all-plants/index.html").read_text(encoding="utf-8")
core=(R/"core-foods/index.html").read_text(encoding="utf-8")
detail=(R/"plant-detail-v56.js").read_text(encoding="utf-8")
css=(R/"plant-detail-v56.css").read_text(encoding="utf-8")
for s in [js,allp,core,detail]:
    assert "🟢" not in s and "🟡" not in s and "🟠" not in s and "🔴" not in s
assert "A (혼합식 활용 가능)" in allp
assert "B (제한적 혼합 급여)" in allp
assert "C (가끔 보조 급여)" in allp
assert "D (급여하지 않음)" in allp
assert "A · 혼합식 활용 가능" in core
assert "B · 제한적 혼합 급여" in core
assert "C · 가끔 보조 급여" in core
assert "D · 급여하지 않음" in core
assert "A','혼합식 활용 가능" in detail
assert "B','제한적으로 혼합 급여" in detail
assert "C','가끔 보조적으로 급여" in detail
assert "D','급여하지 않음" in detail
assert "A/B/C/D는 급여 수준을" in detail
assert "근거등급은 증거의 강도" in detail
assert "../today/" not in js
print("OK: feeding level is expressed as A-D plus parenthetical meaning; evidence grade remains separate")
