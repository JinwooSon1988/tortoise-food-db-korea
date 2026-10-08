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
# Labels are the canonical ones from verdict-core.js / public_verdict.py on every surface.
LABELS=(("A","우선 권장"),("B","조건부 급여"),("C","제한 급여"),("D","급여 제외"))
assert "verdict-core.js" in allp and "TV.display(" in allp, "catalog must take grades from the shared verdict core"
for g,label in LABELS:
    assert f"<i>{g}</i> {label}" in allp, ("catalog legend",g,label)
    assert f"{g} · {label}" in core, ("core-foods legend",g,label)
for src in (verdict,pyv):
    for g,label in LABELS:
        assert g in src and label in src, (g,label)
# Evidence strength (confidence) must never feed into the A-D grade.
assert "confidence" not in verdict and "confidence" not in pyv
assert "../today/" not in js
print("OK: feeding level is expressed as A-D plus parenthetical meaning; evidence grade remains separate")
