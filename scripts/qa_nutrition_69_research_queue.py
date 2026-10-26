#!/usr/bin/env python3
"""Read-only QA for research/nutrition_69_gap_queue_20261016.json."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
def load(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))

def audit():
    queue = load("research/nutrition_69_gap_queue_20261016.json")
    plants = load("data/plants.json")
    verified = load("data/plant_nutrition_v56.json")["plants"]
    references = load("data/plant_nutrition_reference_v1.json")["records"]
    registry = load("data/plant_identity_registry_v1.json")
    aliases = {x["legacy_id"]: x["canonical_id"] for x in registry.get("canonical_aliases", [])}
    plant_ids = {x["id"] for x in plants}
    verified_ids = {x["plant_id"] for x in verified if x.get("verification_status") == "verified"}
    reference_ids = {x["plant_id"] for x in references if x.get("status") == "reference_only" and x.get("feeding_verdict_use") is False}
    rows = queue["records"]
    assert len(rows) == queue["record_count"], "Count mismatch"
    assert len({x["plant_id"] for x in rows}) == len(rows), "Duplicate plant IDs"
    assert all(x["plant_id"] in plant_ids for x in rows), "Unknown plant ID"
    assert all(x["source_state"] == "NOT_LINKED" and x["nutrition_verified"] is False and x["feeding_grade_change"] is False for x in rows), "Research safety gate violated"
    expected = {x["id"] for x in plants if (aliases.get(x["id"], x["id"]) not in verified_ids and aliases.get(x["id"], x["id"]) not in reference_ids)}
    actual = {x["plant_id"] for x in rows}
    assert expected == actual, f"Queue drift: missing={sorted(expected-actual)}, stale={sorted(actual-expected)}"
    print(f"PASS: {len(rows)} research-only gaps match current main data; no feeding verdict changes")

if __name__ == "__main__":
    audit()
