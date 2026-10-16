#!/usr/bin/env python3
"""Evidence-first verdict QA: all public plants retain assessments without nutrition gate."""
import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
plants = json.loads((ROOT / "data/plants.json").read_text(encoding="utf-8"))
assessments = json.loads((ROOT / "data/public_assessments.json").read_text(encoding="utf-8"))
nutrition = json.loads((ROOT / "data/plant_nutrition_v56.json").read_text(encoding="utf-8"))["plants"]
ids = {a["plant_id"] for a in assessments}
assert all(p["id"] in ids for p in plants), "Some plant pages have no feeding assessment"
verified = {n["plant_id"] for n in nutrition if n.get("verification_status") == "verified"}
without_nutrition = {p["id"] for p in plants} - verified
assert without_nutrition, "Test fixture requires nutrition gaps"
code = (ROOT / "scripts/generate_static_pages.py").read_text(encoding="utf-8")
ast.parse(code)
assert 'data-evidence-availability="true"' in code
assert 'data-evidence-availability-en="true"' in code
assert "if pid in nutrition_by_id" in code
assert "verdict_source_html" in code
assert "nutrition_status" in code
print(f"PASS: {len(plants)} pages assessed; {len(without_nutrition)} pages without verified nutrition still eligible for feeding verdict")
