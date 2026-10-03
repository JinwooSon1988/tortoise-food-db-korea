#!/usr/bin/env python3
"""Feeding level is expressed as A-D plus a plain meaning; evidence strength stays separate."""
from pathlib import Path
R=Path(__file__).resolve().parents[1]
js=(R/"public-plant-card-v56.js").read_text(encoding="utf-8")
allp=(R/"all-plants/index.html").read_text(encoding="utf-8")
core=(R/"core-foods/index.html").read_text(encoding="utf-8")
verdict=(R/"verdict-core.js").read_text(encoding="utf-8")
gen=(R/"scripts/generate_static_pages.py").read_text(encoding="utf-8")
pyv=(R/"scripts/public_verdict.py").read_text(encoding="utf-8")
for s in [js,allp,core,verdict,gen,pyv]:
    assert "🟢" not in s and "🟡" not in s and "🟠" not in s and "🔴" not in s
assert "A (혼합식 활용 가능)" in allp
assert "B (제한적 혼합 급여)" in allp
assert "C (가끔 보조 급여)" in allp
assert "D (급여하지 않음)" in allp
assert "A · 혼합식 활용 가능" in core
assert "B · 제한적 혼합 급여" in core
assert "C · 가끔 보조 급여" in core
assert "D · 급여하지 않음" in core
for src in (verdict,pyv):
    for g,label in (("A","혼합식 활용 가능"),("B","제한적 혼합 급여"),("C","가끔 보조 급여"),("D","급여하지 않음")):
        assert g in src and label in src, (g,label)
# Evidence strength (confidence) must never feed into the A-D grade.
assert "confidence" not in verdict and "confidence" not in pyv
assert "../today/" not in js
print("OK: feeding level is expressed as A-D plus parenthetical meaning; evidence grade remains separate")
