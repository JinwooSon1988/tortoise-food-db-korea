#!/usr/bin/env python3
"""Extract pepper candidates from an official USDA FoodData Central CSV export.

Read-only: prints candidate records; never writes verified nutrition.
Usage: python scripts/extract_usda_peppers.py /path/to/unzipped_usda_csv
"""
import csv
import json
import re
import sys
from pathlib import Path

if len(sys.argv) != 2:
    raise SystemExit("Usage: extract_usda_peppers.py <USDA CSV directory>")
folder = Path(sys.argv[1])
for name in ("food.csv", "nutrient.csv", "food_nutrient.csv"):
    if not (folder / name).is_file():
        raise SystemExit(f"Missing USDA CSV file: {name}")
colors = ("green", "orange", "red", "yellow")
matches = {}
with (folder / "food.csv").open(encoding="utf-8-sig", newline="") as f:
    for row in csv.DictReader(f):
        description = (row.get("description") or "").lower()
        if not (re.search(r"\bpeppers?\b", description) and re.search(r"\bbell\b", description) and re.search(r"\braw\b", description)):
            continue
        color = next((c for c in colors if re.search(r"\b" + c + r"\b", description)), None)
        if color is None:
            continue
        fdc_id = row.get("fdc_id")
        if not fdc_id:
            continue
        matches[fdc_id] = {
            "color": color, "fdc_id": fdc_id,
            "description": row.get("description"),
            "data_type": row.get("data_type"),
            "ndb_number": row.get("ndb_number") or None,
            "nutrient_provenance": "USDA CSV candidate; not verified for feeding decisions",
            "nutrients": {},
        }
nutrients = {}
with (folder / "nutrient.csv").open(encoding="utf-8-sig", newline="") as f:
    for row in csv.DictReader(f):
        nutrients[row["id"]] = {"name": row.get("name"), "unit": row.get("unit_name")}
with (folder / "food_nutrient.csv").open(encoding="utf-8-sig", newline="") as f:
    for row in csv.DictReader(f):
        record = matches.get(row.get("fdc_id"))
        if record is None:
            continue
        meta = nutrients.get(row.get("nutrient_id"), {})
        name = meta.get("name")
        amount = row.get("amount")
        if name and amount not in (None, ""):
            key = f"{row.get('nutrient_id')}:{name}"
            record["nutrients"][key] = {"amount": amount, "unit": meta.get("unit"), "nutrient_id": row.get("nutrient_id")}
print(json.dumps({"source": str(folder), "status": "candidate_only", "records": list(matches.values())}, ensure_ascii=False, indent=2))
