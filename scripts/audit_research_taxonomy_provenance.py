#!/usr/bin/env python3
"""Export auditable accepted-name provenance without inferring feeding safety."""
import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

try:
    from scripts.build_research_taxonomy_index import BINOMIAL
except ModuleNotFoundError:
    from build_research_taxonomy_index import BINOMIAL


def audit(accepted, output, report):
    paths = (accepted, output, report)
    if len({p.resolve() for p in paths}) != 3 or output.exists() or report.exists():
        raise ValueError("paths must be distinct and outputs new")
    by_name = defaultdict(set)
    source_rows = 0
    with accepted.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        required = {"plant_scientific_name", "taxonomic_status", "source_reference"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError("missing required accepted-name provenance columns")
        for line_number, row in enumerate(reader, 2):
            name = (row.get("plant_scientific_name") or "").strip()
            status = (row.get("taxonomic_status") or "").strip().lower()
            source = (row.get("source_reference") or "").strip()
            if not BINOMIAL.fullmatch(name) or status != "accepted" or not source:
                raise ValueError(f"invalid accepted-name provenance at row {line_number}")
            source_rows += 1
            by_name[name].add(source)
    if not by_name:
        raise ValueError("empty accepted-name provenance")
    output.parent.mkdir(parents=True, exist_ok=True)
    report.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["plant_scientific_name", "taxonomic_status", "source_reference",
                         "verification_status", "feeding_verdict"])
        for name in sorted(by_name):
            for source in sorted(by_name[name]):
                writer.writerow([name, "accepted", source, "source_claim_unverified", ""])
    counts = {"accepted_input_rows": source_rows, "unique_names": len(by_name),
              "unique_name_source_pairs": sum(map(len, by_name.values())),
              "verification_status": "source_claim_unverified", "feeding_verdict": None}
    with report.open("x", encoding="utf-8") as stream:
        json.dump(counts, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    return counts


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("accepted", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(args.accepted, args.output, args.report), sort_keys=True))
