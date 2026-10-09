#!/usr/bin/env python3
"""Read-only integrity audit of public plant, image and nutrition coverage."""
import json
import pathlib
import sys
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parents[1]

def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))

def main():
    plants = read("data/plants.json")
    images = read("data/verified_plant_images_v56.json")["images"]
    holds = read("data/nutrition_hold_list_v1.json")["records"]
    nutrition = read("data/nutrition_coverage_audit_v1.json")
    errors = []
    plant_ids = [p["id"] for p in plants]
    plant_set = set(plant_ids)
    image_ids = [x["plant_id"] for x in images]
    hold_ids = [x["plant_id"] for x in holds]
    for label, ids in (("plants", plant_ids), ("images", image_ids), ("nutrition holds", hold_ids)):
        duplicates = sorted(k for k, v in Counter(ids).items() if v > 1)
        if duplicates:
            errors.append(f"duplicate {label} IDs: {duplicates}")
    for label, ids in (("images", image_ids), ("nutrition holds", hold_ids)):
        extra = sorted(set(ids) - plant_set)
        if extra:
            errors.append(f"unknown {label} plant IDs: {extra}")
    for image in images:
        for key in ("source_url", "creator", "license", "image_url"):
            if not image.get(key):
                errors.append(f"image {image['plant_id']} missing {key}")
        if image.get("part_match") not in ("match", "partial", "mismatch"):
            errors.append(f"image {image['plant_id']} invalid part_match")
    if len(plants) != nutrition["public_plants"]:
        errors.append("public plant count differs from nutrition audit")
    if len(holds) != nutrition["held_plants"]:
        errors.append("nutrition hold count differs from nutrition audit")
    if len(plants) - len(holds) != nutrition["verified_plants"]:
        errors.append("nutrition verified count differs from nutrition audit")
    # Same Korean label and scientific taxon under multiple IDs can fragment search results.
    taxon_labels = {}
    for plant in plants:
        key = (plant.get("ko", "").strip(), plant.get("scientific", "").strip())
        taxon_labels.setdefault(key, []).append(plant["id"])
    duplicate_concepts = [
        {"ko": ko, "scientific": scientific, "plant_ids": ids}
        for (ko, scientific), ids in sorted(taxon_labels.items()) if len(ids) > 1
    ]
    statuses = Counter(x.get("part_match") for x in images)
    reasons = Counter(x.get("hold_reason_code") for x in holds)
    image_part_mismatches = [
        {"plant_id": x["plant_id"], "scientific": x.get("scientific"),
         "depicted_part": x.get("depicted_part"), "source_url": x.get("source_url")}
        for x in images if x.get("part_match") == "mismatch"
    ]
    image_part_partial = sorted(
        x["plant_id"] for x in images if x.get("part_match") == "partial"
    )
    plants_without_images = sorted(plant_set - set(image_ids))
    # Ambiguous market names must not silently override canonical taxon.
    alias_taxon_review = [
        {"plant_id": p["id"], "scientific": p.get("scientific"),
         "aliases": p.get("aliases", []),
         "issue": "Korean aehobak and zucchini are not interchangeable cultivar identities"}
        for p in plants
        if p["id"] == "zucchini"
        and p.get("scientific") == "Cucurbita moschata"
        and "zucchini" in [a.lower() for a in p.get("aliases", [])]
    ]
    print(json.dumps({
        "plants": len(plants), "images": len(images),
        "images_missing": len(plant_set - set(image_ids)),
        "image_part_status": dict(statuses),
        "nutrition_verified": nutrition["verified_plants"],
        "nutrition_held": len(holds),
        "nutrition_hold_reasons": dict(reasons),
        "duplicate_taxon_label_concepts_review_only": duplicate_concepts,
        "image_part_mismatches_needing_replacement": image_part_mismatches,
        "image_part_partial_needing_review": image_part_partial,
        "plants_without_image": plants_without_images,
        "ambiguous_alias_taxon_review_only": alias_taxon_review,
        "errors": errors,
        "result": "PASS" if not errors else "FAIL"
    }, ensure_ascii=False, indent=2))
    return 1 if errors else 0

if __name__ == "__main__":
    sys.exit(main())
