#!/usr/bin/env python3
"""Export a provenance-preserving bulk literature review sheet; never infer safety."""
import argparse
import csv
import json
from pathlib import Path

COLUMNS = ("source_database", "source_record_id", "doi", "source_url", "source_title",
           "review_priority", "plant_diet_context_excerpts", "unverified_binomial_strings",
           "review_status", "verified_plant_scientific_name",
           "verified_tortoise_scientific_name", "verified_plant_part",
           "observation_type", "reviewer_notes", "reviewed_at", "evidence_quote")


def export_queue(input_path, output_path):
    if input_path.resolve() == output_path.resolve() or output_path.exists():
        raise ValueError("output must be new and distinct")
    rows = []
    seen = set()
    with input_path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict) or row.get("review_status") != "manual_validation_required":
                raise ValueError(f"invalid review lead at line {line_number}")
            key = (row.get("source_database"), row.get("source_record_id"))
            if not all(isinstance(v, str) and v.strip() for v in key):
                raise ValueError(f"missing provenance at line {line_number}")
            if key in seen:
                raise ValueError(f"duplicate literature identifier at line {line_number}")
            seen.add(key)
            if row.get("feeding_verdict") is not None:
                raise ValueError(f"unverified record has verdict at line {line_number}")
            rows.append({
                "source_database": key[0], "source_record_id": key[1],
                "doi": row.get("doi") or "", "source_url": row.get("source_url") or "",
                "source_title": row.get("source_title") or "",
                "review_priority": row.get("review_priority") or "",
                "plant_diet_context_excerpts": " | ".join(row.get("plant_diet_context_excerpts") or []),
                "unverified_binomial_strings": " | ".join(row.get("unverified_binomial_strings") or []),
                "review_status": "manual_validation_required",
                "verified_plant_scientific_name": "", "verified_tortoise_scientific_name": "",
                "verified_plant_part": "", "observation_type": "", "reviewer_notes": "",
                "reviewed_at": "", "evidence_quote": ""}
    if not rows:
        raise ValueError("no records to export")
    rows.sort(key=lambda x: (x["review_priority"] != "abstract_review",
                             x["source_database"], x["source_record_id"]))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("x", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return {"review_rows": len(rows), "priority_rows": sum(x["review_priority"] == "abstract_review" for x in rows)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(export_queue(args.input, args.output), sort_keys=True))
