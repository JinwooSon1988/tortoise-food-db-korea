#!/usr/bin/env python3
"""Fast CI checks for lettuce variety records; original USDA ZIP audited separately."""
import json
import math
from pathlib import Path

root = Path(__file__).resolve().parents[1]
data = json.loads((root / "data/plant_nutrition_variety_v1.json").read_text(encoding="utf-8"))
master = json.loads((root / "data/plant_nutrition_v56.json").read_text(encoding="utf-8"))
assert data["feeding_verdict_use"] is False
assert len(data["records"]) == 5
assert {r["fdc_id"] for r in data["records"]} == {168429,168431,169247,169248,169249}
assert not any(r["plant_id"] == "lettuce" for r in master["plants"]), "Variety records improperly promoted to master"
for r in data["records"]:
    assert r["plant_id"] == "lettuce" and r["scientific_name"] == "Lactuca sativa"
    assert r["preparation_state"] == "raw"
    assert r["source_url"] == f'https://fdc.nal.usda.gov/food-details/{r["fdc_id"]}/nutrients'
    assert all(math.isfinite(r[k]) and r[k] >= 0 for k in ("calcium_mg", "phosphorus_mg", "calcium_phosphorus_ratio")), "Invalid or nonfinite nutrition value"
    assert r["phosphorus_mg"] > 0
    assert abs(r["calcium_phosphorus_ratio"] - r["calcium_mg"] / r["phosphorus_mg"]) < .001
print("PASS (internal consistency only; USDA source ZIP not checked): 5 lettuce variety identities, source URLs, ratios and master isolation")
