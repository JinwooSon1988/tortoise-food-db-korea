#!/usr/bin/env python3
"""Bulk export strictly matched GBIF plant candidates for manual evidence review."""
import argparse
import csv
from pathlib import Path

REQUIRED = {"openalex_id", "candidate_binomial", "gbif_status", "gbif_taxon_key",
            "gbif_scientific_name", "feeding_keyword_windows", "sample_context"}
FIELDS = ["candidate_binomial", "gbif_taxon_key", "gbif_scientific_name",
          "unique_papers", "feeding_keyword_papers", "openalex_papers",
          "sample_context", "full_text_checked", "feeding_confirmed", "safety_verdict"]


def build_queue(rows):
    grouped = {}
    for row in rows:
        if row["gbif_status"] != "exact_plant_taxon_candidate":
            continue
        name = row["candidate_binomial"].strip()
        key = row["gbif_taxon_key"].strip()
        paper = row["openalex_id"].strip()
        if not name or not key.isdecimal() or not paper.startswith("https://openalex.org/W"):
            continue
        identifier = (key, name.casefold())
        entry = grouped.setdefault(identifier, {"candidate_binomial": name,
            "gbif_taxon_key": key, "gbif_scientific_name": row["gbif_scientific_name"],
            "papers": set(), "keyword_papers": set(), "sample_context": row["sample_context"]})
        entry["papers"].add(paper)
        try:
            if int(row["feeding_keyword_windows"]) > 0:
                entry["keyword_papers"].add(paper)
        except ValueError:
            pass
    result = []
    for entry in grouped.values():
        result.append({**{k: entry[k] for k in FIELDS[:3]},
            "unique_papers": len(entry["papers"]),
            "feeding_keyword_papers": len(entry["keyword_papers"]),
            "openalex_papers": " | ".join(sorted(entry["papers"])),
            "sample_context": entry["sample_context"],
            "full_text_checked": "no",
            "feeding_confirmed": "unverified",
            "safety_verdict": "not_assessed"})
    return sorted(result, key=lambda r: (-r["feeding_keyword_papers"],
                                          -r["unique_papers"], r["candidate_binomial"]))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.input.resolve() == args.output.resolve():
        parser.error("input and output must differ")
    with args.input.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not REQUIRED.issubset(reader.fieldnames or []):
            parser.error("missing required columns")
        queue = build_queue(reader)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(queue)
    print(f"exact_plant_review_candidates={len(queue)}")


if __name__ == "__main__":
    main()
