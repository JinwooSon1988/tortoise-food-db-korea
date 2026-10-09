#!/usr/bin/env python3
"""Reproduce USDA mint-candidate values from the official SR Legacy CSV archive.

Usage:
  python scripts/audit_usda_mint_candidates.py \
    /path/to/FoodData_Central_sr_legacy_food_csv_2018-04.zip
"""
import csv
import io
import json
import sys
import zipfile
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data/usda_mint_variety_candidates_20261009.json"
FIELDS = {
    "water_g": "1051",
    "protein_g": "1003",
    "fiber_g": "1079",
    "calcium_mg": "1087",
    "phosphorus_mg": "1091",
    "potassium_mg": "1092",
    "vitamin_c_mg": "1162",
}


def csv_rows(archive, suffix):
    member = next((n for n in archive.namelist() if n.endswith("/" + suffix)), None)
    if member is None:
        raise ValueError(f"Missing USDA CSV member: {suffix}")
    with archive.open(member) as raw:
        yield from csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8-sig"))


def main(archive_path):
    data = json.loads(DATA.read_text(encoding="utf-8"))
    records = {str(r["fdc_id"]): r for r in data["records"]}
    with zipfile.ZipFile(archive_path) as archive:
        descriptions = {
            r["fdc_id"]: r["description"]
            for r in csv_rows(archive, "food.csv")
            if r["fdc_id"] in records
        }
        amounts = {}
        for row in csv_rows(archive, "food_nutrient.csv"):
            if row["fdc_id"] in records and row["nutrient_id"] in FIELDS.values():
                key = (row["fdc_id"], row["nutrient_id"])
                if key in amounts:
                    raise AssertionError(f"Duplicate nutrient record: {key}")
                amounts[key] = float(row["amount"])
    for fdc_id, record in records.items():
        assert descriptions.get(fdc_id) == record["food_description"], (
            f"Food description mismatch: {fdc_id}"
        )
        assert record["master_eligible"] is False, "Unresolved identity must remain held"
        assert record["feeding_verdict_use"] is False, "Nutrients cannot set feeding verdict"
        for field, nutrient_id in FIELDS.items():
            actual = amounts.get((fdc_id, nutrient_id))
            expected = float(record[field])
            assert actual is not None and abs(actual - expected) < 1e-9, (
                f"{fdc_id} {field}: CSV={actual} stored={expected}"
            )
    print(f"PASS: {len(records)} USDA mint foods, {len(records) * len(FIELDS)} original CSV nutrient values; both held from master and feeding verdict")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage: python scripts/audit_usda_mint_candidates.py SR_LEGACY.zip")
    main(sys.argv[1])
