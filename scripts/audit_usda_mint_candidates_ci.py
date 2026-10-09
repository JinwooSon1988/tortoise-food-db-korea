#!/usr/bin/env python3
"""CI guard for USDA mint candidates. Full source audit needs original USDA ZIP."""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
data = json.loads((root / "data/usda_mint_variety_candidates_20261009.json").read_text(encoding="utf-8"))
master = json.loads((root / "data/plant_nutrition_v56.json").read_text(encoding="utf-8"))
assert data["website_taxon"] == "Mentha spp."
assert len(data["records"]) == 2
assert {r["fdc_id"] for r in data["records"]} == {173474, 173475}
assert not any(r["plant_id"] == "mint" for r in master["plants"]), "Unresolved mint promoted to master"
for r in data["records"]:
    assert r["plant_id"] == "mint"
    assert r["master_eligible"] is False
    assert r["feeding_verdict_use"] is False
    assert r["source_url"] == f'https://fdc.nal.usda.gov/food-details/{r["fdc_id"]}/nutrients'
    assert r["calcium_mg"] > 0 and r["phosphorus_mg"] > 0
    assert abs(r["calcium_phosphorus_ratio"] - r["calcium_mg"] / r["phosphorus_mg"]) < .001
print("PASS: USDA mint candidate identity/part hold, master exclusion, links and ratio consistency")
