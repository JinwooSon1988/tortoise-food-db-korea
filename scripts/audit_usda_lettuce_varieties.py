#!/usr/bin/env python3
"""Check five lettuce varieties against the original USDA SR Legacy 2018-04 CSV.

Usage: python scripts/audit_usda_lettuce_varieties.py /path/to/FoodData_Central_sr_legacy_food_csv_2018-04.zip
"""
import csv
import io
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIELDS = {
    "water_g": "1051", "protein_g": "1003", "fiber_g": "1079",
    "calcium_mg": "1087", "phosphorus_mg": "1091",
    "potassium_mg": "1092", "vitamin_c_mg": "1162",
}

def rows(z, filename):
    member = next((name for name in z.namelist() if name.endswith("/" + filename)), None)
    if member is None:
        raise RuntimeError(f"Missing official USDA member: {filename}")
    with z.open(member) as stream:
        yield from csv.DictReader(io.TextIOWrapper(stream, encoding="utf-8-sig"))

def main(path):
    data = json.loads((ROOT / "data/plant_nutrition_variety_v1.json").read_text(encoding="utf-8"))
    expected = {str(r["fdc_id"]): r for r in data["records"]}
    assert len(expected) == 5 and len(data["records"]) == 5
    assert data["feeding_verdict_use"] is False
    with zipfile.ZipFile(path) as z:
        food = {r["fdc_id"]: r["description"] for r in rows(z, "food.csv") if r["fdc_id"] in expected}
        amounts = {}
        for row in rows(z, "food_nutrient.csv"):
            key = (row["fdc_id"], row["nutrient_id"])
            if key[0] in expected and key[1] in FIELDS.values():
                assert key not in amounts, f"Duplicate USDA nutrient {key}"
                amounts[key] = float(row["amount"])
    for fdc, record in expected.items():
        assert food.get(fdc) == record["food_description"], f"Food name mismatch: {fdc}"
        assert record["plant_id"] == "lettuce" and record["preparation_state"] == "raw"
        for field, nutrient in FIELDS.items():
            actual = amounts.get((fdc, nutrient))
            assert actual is not None and abs(actual - float(record[field])) < 1e-9, (
                f"{fdc} {field}: USDA={actual} stored={record[field]}"
            )
        assert abs(record["calcium_phosphorus_ratio"] - record["calcium_mg"] / record["phosphorus_mg"]) < .001
    print("PASS: 5 lettuce USDA food identities and 35 numeric nutrient values match original CSV")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage: python scripts/audit_usda_lettuce_varieties.py SR_LEGACY.zip")
    main(sys.argv[1])
