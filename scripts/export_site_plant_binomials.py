#!/usr/bin/env python3
"""Export existing site catalog binomials for conservative literature matching."""
import argparse
import csv
import json
import re
from pathlib import Path

BINOMIAL = re.compile(r"^([A-Z][a-z]+ [a-z][a-z-]+)(?: (?:var\\.|subsp\\.|ssp\\.) [a-z][a-z-]+)?$")


def export(catalog, output):
    if catalog.resolve() == output.resolve() or output.exists():
        raise ValueError("output must be new and distinct")
    records = json.loads(catalog.read_text(encoding="utf-8"))
    if not isinstance(records, list):
        raise ValueError("catalog must be a list")
    names = set()
    skipped = 0
    normalized_infraspecific = 0
    for record in records:
        name = record.get("scientific") if isinstance(record, dict) else None
        match = BINOMIAL.fullmatch(name.strip()) if isinstance(name, str) else None
        if match:
            names.add(match.group(1))
            normalized_infraspecific += name.strip() != match.group(1)
        else:
            skipped += 1
    if not names:
        raise ValueError("no valid plant binomials in catalog")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["plant_scientific_name"])
        writer.writerows([[name] for name in sorted(names)])
    return {"catalog_records": len(records), "unique_valid_binomials": len(names),
            "skipped_non_binomials": skipped,
            "normalized_infraspecific_records": normalized_infraspecific}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("catalog", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(export(args.catalog, args.output), sort_keys=True))
