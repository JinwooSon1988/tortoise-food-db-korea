#!/usr/bin/env python3
"""Verify that the photo replacement queue tracks every unapproved plant image."""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
read = lambda path: json.loads((root / path).read_text(encoding="utf-8"))
plants = read("data/plants.json")
images = read("data/verified_plant_images_v56.json")["images"]
queue = read("data/plant_image_replacement_queue_v1.json")["records"]
approved = {item["plant_id"] for item in images if item.get("part_match") == "match" and item.get("identity_scope") in ("exact_species", "exact_subspecies", "exact_variety")}
expected = {p["id"] for p in plants if p["id"] not in approved}
actual = [item["id"] for item in queue]
assert len(actual) == len(set(actual)), "Duplicate queue IDs"
assert set(actual) == expected, "Queue missing or retaining plants inconsistent with approved images"
for item in queue:
    assert item["issue"] in ("partial_part_match", "no_approved_image"), item
    assert item.get("scientific") and item.get("en"), item
print(f"PASS: {len(queue)} image replacements tracked; {len(approved)} approved plant images")
