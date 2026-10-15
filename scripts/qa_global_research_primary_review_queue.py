#!/usr/bin/env python3
"""Verify the 102-row primary-reference review queue against its research source."""
import csv
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
records = json.loads((root / "data/research/tortoise_plant_evidence_v1.json").read_text(encoding="utf-8"))["records"]
expected = {r["evidence_id"]: r for r in records if r["evidence_directness"] == "reported_in_account_primary_not_read"}
with (root / "data/research/primary_reference_review_queue_20261014.csv").open(encoding="utf-8", newline="") as handle:
    rows = list(csv.DictReader(handle))
assert len(expected) == 102, f"Unexpected research baseline: {len(expected)}"
assert len(rows) == len(expected), f"Queue rows {len(rows)} != {len(expected)}"
ids = [row["evidence_id"] for row in rows]
assert len(ids) == len(set(ids)), "Duplicate evidence IDs in review queue"
assert set(ids) == set(expected), "Queue does not match all secondary research evidence IDs"
for row in rows:
    original = expected[row["evidence_id"]]
    for key in ("tortoise_scientific_name", "plant_accepted_name", "plant_part", "primary_reference_cited_by_source", "source_url", "source_page"):
        assert row[key] == str(original.get(key) or ""), f"{row['evidence_id']}: source mismatch for {key}"
    for key in ("primary_fulltext_url", "primary_exact_locator", "review_outcome", "reviewer_notes"):
        assert not row[key].strip(), f"{row['evidence_id']}: unverified field was prefilled: {key}"
print("Primary-source review queue verified: 102 unique, source-matched, unverified records")
