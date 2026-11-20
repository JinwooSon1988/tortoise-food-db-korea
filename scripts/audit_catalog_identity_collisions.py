#!/usr/bin/env python3
"""Audit catalog identity collisions without deleting legitimate plant-part entries."""
import argparse
import json
from collections import defaultdict
from pathlib import Path


def audit(catalog, report):
    if catalog.resolve() == report.resolve() or report.exists():
        raise ValueError("report must be new and distinct")
    records = json.loads(catalog.read_text(encoding="utf-8"))
    if not isinstance(records, list):
        raise ValueError("catalog must be a list")
    by_scientific = defaultdict(list)
    ids = set()
    for number, item in enumerate(records, 1):
        if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not item["id"]:
            raise ValueError(f"invalid catalog identity at record {number}")
        if item["id"] in ids:
            raise ValueError(f"duplicate catalog id: {item['id']}")
        ids.add(item["id"])
        name = item.get("scientific")
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"missing scientific name at record {number}")
        by_scientific[name.strip()].append({"id": item["id"], "ko": item.get("ko"),
                                            "en": item.get("en")})
    collisions = []
    for name, entries in sorted(by_scientific.items()):
        if len(entries) < 2:
            continue
        labels = [(entry["ko"], entry["en"]) for entry in entries]
        collisions.append({
            "scientific": name, "records": entries,
            "identical_display_labels": len(labels) != len(set(labels)),
            "review_status": "human_review_required",
            "note": "Shared taxon may represent different plant parts; never auto-merge."})
    result = {
        "catalog_records": len(records), "distinct_scientific_strings": len(by_scientific),
        "shared_scientific_name_groups": len(collisions),
        "shared_scientific_name_records": sum(len(x["records"]) for x in collisions),
        "potential_identical_display_label_groups": sum(x["identical_display_labels"] for x in collisions),
        "collisions": collisions, "feeding_verdict": None}
    report.parent.mkdir(parents=True, exist_ok=True)
    with report.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("catalog", type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    result = audit(args.catalog, args.report)
    print(json.dumps({key: value for key, value in result.items() if key != "collisions"},
                     ensure_ascii=False, sort_keys=True))
