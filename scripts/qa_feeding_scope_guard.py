#!/usr/bin/env python3
"""Guard against accidental expansion of plant-part and evidence scope.

This QA does not adjudicate feeding grades. Nutrition data is out of scope.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
assessments = json.loads((ROOT / "data/public_assessments.json").read_text(encoding="utf-8"))
keys = [(item["plant_id"], item["species_group"]) for item in assessments]
assert len(set(keys)) == len(keys), "Duplicate plant_id + species_group in public assessments"
by_id = {item["plant_id"]: item for item in assessments if item["species_group"] == "Tortoise_general"}

# Species-group records are intentionally separate, not accidental duplicates.
required_species_group_records = {
    ("dandelion", "Mediterranean_Testudo"),
    ("dandelion", "Sulcata"),
    ("plantain", "Mediterranean_Testudo"),
    ("plantain", "Sulcata"),
    ("clover", "Mediterranean_Testudo"),
    ("clover", "Sulcata"),
    ("chickweed", "Mediterranean_Testudo"),
    ("chickweed", "Sulcata"),
}
by_group = {(item["plant_id"], item["species_group"]): item for item in assessments}
assert len(assessments) >= 186, "Assessment records dropped below the audited baseline (186)"
assert len({item["plant_id"] for item in assessments}) >= 182, "Plant coverage dropped below the audited baseline (182)"
for key in required_species_group_records:
    assert key in by_group, f"Missing species-specific assessment: {key}"
    assert by_group[key].get("verdict"), f"Species-specific verdict missing: {key}"
    assert by_group[key].get("evidence_ids"), f"Missing evidence references: {key}"
    assert by_group[key].get("why", "").strip(), f"Missing feeding rationale: {key}"

# The same plant can have different roles in Testudo and Sulcata diets.
assert "혼합식" in by_group[("dandelion", "Mediterranean_Testudo")]["why"]
assert "풀·건초" in by_group[("dandelion", "Sulcata")]["why"]

def check(plant_id, required_phrases):
    item = by_id[plant_id]
    assert item.get("verdict"), f"{plant_id}: missing verdict"
    assert item.get("evidence_ids"), f"{plant_id}: missing evidence references"
    assert item.get("why", "").strip(), f"{plant_id}: missing rationale"
    text = " ".join([item.get("why", ""), item.get("applicability_note", ""), *item.get("limits", [])])
    for phrase in required_phrases:
        assert phrase in text, f"{plant_id}: missing critical scope caveat: {phrase}"

check("bellpepper", ["급여하지 않음", "육지거북 급여 안전성 시험이 아님", "잎·줄기"])
check("peachleaf", ["추출물", "육지거북에게 먹여 본 시험"])
check("mapleleaf", ["Acer", "씨앗·수피"])
check("dahlia", ["뿌리·괴경", "잎·꽃"])
print("PASS: assessment scope caveats preserved; disputed verdicts are not frozen by QA")
