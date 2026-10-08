#!/usr/bin/env python3
"""Audit source-verified pepper nutrition without assigning tortoise feeding grades."""
import json
from pathlib import Path
root = Path(__file__).resolve().parents[1]
data = json.loads((root / "data/usda_bellpepper_original_csv_verified_20261008.json").read_text(encoding="utf-8"))
records = data["records"]
assert data["status"] == "nutrition_source_verified__feeding_grade_not_assessed"
assert len(records) == 7
assert len({r["fdc_id"] for r in records}) == 7
expected = {
    ("Foundation", "green"): 2258588,
    ("Foundation", "yellow"): 2258589,
    ("Foundation", "red"): 2258590,
    ("Foundation", "orange"): 2258591,
    ("SR Legacy", "yellow"): 169383,
    ("SR Legacy", "red"): 170108,
    ("SR Legacy", "green"): 170427,
}
assert {(r["data_type"], r["color"]): r["fdc_id"] for r in records} == expected
for r in records:
    ca, p = r["calcium_mg_per_100g"], r["phosphorus_mg_per_100g"]
    assert isinstance(ca, (int, float)) and isinstance(p, (int, float)) and ca >= 0 and p > 0
    assert abs(r["ca_p_ratio"] - round(ca / p, 3)) < 1e-9
    assert r["source_url"] == f"https://fdc.nal.usda.gov/food-details/{r['fdc_id']}/nutrients"
    assert "feeding_grade" not in r and "suitability" not in r
print("OK: seven USDA pepper records have distinct FDC IDs, correct ratios and no feeding grades")
