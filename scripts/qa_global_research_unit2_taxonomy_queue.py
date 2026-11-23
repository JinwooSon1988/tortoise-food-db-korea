#!/usr/bin/env python3
"""Ensure unresolved Unit 2 taxonomy review queue is complete and unverified."""
import csv
import json
import re
from pathlib import Path

root = Path(__file__).resolve().parents[1]
records = json.loads((root / "data/research/tortoise_plant_evidence_v2.json").read_text(encoding="utf-8"))["records"]
expected = {r["evidence_id"]: r for r in records if re.search(r"conflict|homonym|needs_review|unresolved", r.get("plant_name_check") or "", re.I)}
with (root / "data/research/unit2_taxonomy_review_queue_20261014.csv").open(encoding="utf-8", newline="") as file:
    rows = list(csv.DictReader(file))
errors = []
if len(expected) != 25:
    errors.append(f"Expected 25 unresolved source records, got {len(expected)}")
if len(rows) != len(expected):
    errors.append(f"Expected {len(expected)} review rows, got {len(rows)}")
ids = [r["evidence_id"] for r in rows]
if len(ids) != len(set(ids)) or set(ids) != set(expected):
    errors.append("Taxonomy review IDs missing, duplicated or unexpected")
for row in rows:
    original = expected.get(row["evidence_id"])
    if original is None:
        continue
    for field in ("tortoise_scientific_name", "plant_name_as_printed", "plant_accepted_name", "plant_name_check", "plant_part", "source_url", "source_page"):
        if row[field] != str(original.get(field) or ""):
            errors.append(f"{row['evidence_id']}: source mismatch in {field}")
    for field in ("reviewed_primary_page", "taxonomic_resolution", "review_status", "review_notes"):
        if row[field].strip():
            errors.append(f"{row['evidence_id']}: unverified review field prefilled: {field}")
if errors:
    raise SystemExit("\n".join(errors))
print(f"Unit 2 taxonomy review queue passed: {len(rows)} unresolved records, zero claimed resolutions")
