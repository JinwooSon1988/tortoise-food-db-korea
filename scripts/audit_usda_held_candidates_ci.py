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
# The held USDA records themselves must never become master nutrition. A plant may still be verified from a
# different exact-taxon source (amaranthleaf: RDA 비름 via korea_taxon_mapping_v1), never from these FDC IDs.
for r in master["plants"]:
    if r["plant_id"] in ids:
        assert r["source_name"] != "USDA FoodData Central", f'{r["plant_id"]}: held USDA candidate promoted'
        assert str(ids[r["plant_id"]]) not in r["source_id"], f'{r["plant_id"]}: held FDC ID used as master source'
held_in_master = {r["plant_id"] for r in master["plants"]} & set(ids)
korea = {x["plant_id"] for x in json.loads((root / "data/korea_taxon_mapping_v1.json").read_text(encoding="utf-8"))["records"]
         if x.get("nutrition_mapping_status") == "eligible_exact_korea_taxon"}
assert held_in_master <= korea, f"plants verified without an exact Korea taxon mapping: {sorted(held_in_master - korea)}"
for r in data["records"]:
    assert r["fdc_id"] == ids[r["plant_id"]]
    assert r["promotion_status"] == "HOLD_identity_or_part_match"
    assert r["identity_limit"].strip()
    assert r["source_url"] == f'https://fdc.nal.usda.gov/food-details/{r["fdc_id"]}/nutrients'
    assert r["phosphorus_mg"] > 0
    assert abs(r["ca_p_ratio"] - r["calcium_mg"] / r["phosphorus_mg"]) < .001
    if r["fiber_g"] is None:
        assert r["plant_id"] in {"borage", "amaranthleaf"}
print("PASS: four source-backed USDA candidates remain held for species/part identity; none is a master nutrition source")
