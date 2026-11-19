#!/usr/bin/env python3
"""Merge reviewed accepted botanical identities into a research-only matching index."""
import argparse
import csv
import json
import re
from pathlib import Path

BINOMIAL = re.compile(r"^[A-Z][a-z]+ [a-z][a-z-]+$")
MAX_TERMS = 100000


def build(catalog, accepted, output, report):
    paths = (catalog, accepted, output, report)
    if len({p.resolve() for p in paths}) != 4 or output.exists() or report.exists():
        raise ValueError("inputs/outputs must be distinct and outputs new")
    names = set()
    counts = {"catalog_rows": 0, "accepted_rows": 0, "duplicates": 0}
    for path, origin in ((catalog, "catalog"), (accepted, "accepted")):
        with path.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            required = {"plant_scientific_name"} if origin == "catalog" else {
                "plant_scientific_name", "taxonomic_status", "source_reference"}
            if not reader.fieldnames or not required.issubset(reader.fieldnames):
                raise ValueError(f"{origin} CSV missing required columns")
            for line_number, row in enumerate(reader, 2):
                name = (row.get("plant_scientific_name") or "").strip()
                if not BINOMIAL.fullmatch(name):
                    raise ValueError(f"invalid binomial at {origin} row {line_number}")
                if origin == "accepted":
                    if (row.get("taxonomic_status") or "").strip().lower() != "accepted":
                        raise ValueError(f"unaccepted taxon at row {line_number}")
                    if not (row.get("source_reference") or "").strip():
                        raise ValueError(f"missing taxonomy source at row {line_number}")
                counts[f"{origin}_rows"] += 1
                if name in names:
                    counts["duplicates"] += 1
                names.add(name)
                if len(names) > MAX_TERMS:
                    raise ValueError("taxonomy limit exceeded")
    if not names:
        raise ValueError("empty taxonomy")
    output.parent.mkdir(parents=True, exist_ok=True)
    report.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["plant_scientific_name"])
        writer.writerows((name,) for name in sorted(names))
    counts["unique_binomials"] = len(names)
    with report.open("x", encoding="utf-8") as stream:
        json.dump({"counts": counts, "purpose": "research_only_exact_name_matching",
                   "feeding_verdict": None}, stream, indent=2)
        stream.write("\n")
    return counts


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("catalog", type=Path, help="Existing site binomial CSV")
    parser.add_argument("accepted", type=Path, help="Externally verified accepted-name CSV")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.catalog, args.accepted, args.output, args.report), sort_keys=True))
