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

def check(plant_id, expected_verdict, required_phrases):
    item = by_id[plant_id]
    assert item["verdict"] == expected_verdict, f"{plant_id}: grade changed; re-review source evidence and QA"
    text = " ".join([item.get("why", ""), item.get("applicability_note", ""), *item.get("limits", [])])
    for phrase in required_phrases:
        assert phrase in text, f"{plant_id}: missing critical scope caveat: {phrase}"

check("bellpepper", "limited_supplement", ["급여하지 않음", "육지거북 급여 안전성 시험이 아님", "잎·줄기"])
check("peachleaf", "limited_supplement", ["추출물", "육지거북에게 먹여 본 시험"])
check("mapleleaf", "limited_supplement", ["Acer", "씨앗·수피"])
check("dahlia", "limited_supplement", ["뿌리·괴경", "잎·꽃"])
print("PASS: four assessment scope caveats preserved; grade conflicts still require editorial review")
