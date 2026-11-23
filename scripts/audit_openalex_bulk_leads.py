#!/usr/bin/env python3
"""Audit OpenAlex bulk research leads; never infer feeding safety from search hits."""
import argparse
import json
from pathlib import Path


def audit(path):
    latest = {}
    attempts = 0
    with path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                raise ValueError(f"blank checkpoint row {line_number}")
            try:
                row = json.loads(line)
            except ValueError as exc:
                raise ValueError(f"invalid JSONL row {line_number}") from exc
            if not isinstance(row, dict) or row.get("status") not in ("searched", "retry_needed"):
                raise ValueError(f"invalid checkpoint status at row {line_number}")
            name = row.get("name")
            if not isinstance(name, str) or not name.strip():
                raise ValueError(f"missing taxon name at row {line_number}")
            if not isinstance(row.get("hits"), list):
                raise ValueError(f"invalid hits at row {line_number}")
            if row["status"] == "searched" and any(
                not isinstance(hit, dict) or hit.get("status") != "literature_lead_unreviewed"
                for hit in row["hits"]
            ):
                raise ValueError(f"unreviewed evidence status violation at row {line_number}")
            attempts += 1
            key = name.casefold()
            # Never let a later retry_needed record erase a successful prior search.
            if key not in latest or row["status"] == "searched":
                latest[key] = row
    works = set()
    total_hits = 0
    completed = 0
    with_hits = 0
    for row in latest.values():
        if row["status"] != "searched":
            continue
        completed += 1
        hits = row["hits"]
        total_hits += len(hits)
        with_hits += bool(hits)
        for hit in hits:
            identifier = hit.get("openalex_id") or hit.get("doi")
            if isinstance(identifier, str) and identifier.strip():
                works.add(identifier.strip().casefold())
    return {
        "scope": "unreviewed_literature_leads_only",
        "feeding_verdicts_confirmed": 0,
        "attempt_rows": attempts,
        "unique_taxa_attempted": len(latest),
        "unique_taxa_searched": completed,
        "unique_taxa_retry_needed": len(latest) - completed,
        "taxa_with_search_hits": with_hits,
        "total_hit_occurrences": total_hits,
        "distinct_identified_works": len(works),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("checkpoint", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    result = audit(args.checkpoint)
    output = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.report:
        if args.report.resolve() == args.checkpoint.resolve():
            parser.error("report must not overwrite the checkpoint")
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(output, encoding="utf-8")
    print(output, end="")


if __name__ == "__main__":
    main()
