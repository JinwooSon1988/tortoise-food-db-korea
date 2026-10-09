#!/usr/bin/env python3
"""Prevent unresolved USDA species/part candidates from becoming verified nutrition."""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
data = json.loads((root / "data/usda_srlegacy_plant_candidates_batch2_20261008.json").read_text(encoding="utf-8"))
master = json.loads((root / "data/plant_nutrition_v56.json").read_text(encoding="utf-8"))
ids = {"borage": 170481, "amaranthleaf": 168385, "grapevineleaf": 168575, "opuntiapad": 168571}
assert len(data["records"]) == len(ids)
assert data["review_matrix_20261009"]["verified_master_eligible"] == 0
assert {r["plant_id"] for r in data["review_matrix_20261009"]["candidates"]} == set(ids)
assert not set(ids).intersection(r["plant_id"] for r in master["plants"]), "Held plant in verified master"
for r in data["records"]:
    assert r["fdc_id"] == ids[r["plant_id"]]
    assert r["promotion_status"] == "HOLD_identity_or_part_match"
    assert r["identity_limit"].strip()
    assert r["source_url"] == f'https://fdc.nal.usda.gov/food-details/{r["fdc_id"]}/nutrients'
    assert r["phosphorus_mg"] > 0
    assert abs(r["ca_p_ratio"] - r["calcium_mg"] / r["phosphorus_mg"]) < .001
    if r["fiber_g"] is None:
        assert r["plant_id"] in {"borage", "amaranthleaf"}
print("PASS: four source-backed USDA candidates remain held for species/part identity")
