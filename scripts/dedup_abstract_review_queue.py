#!/usr/bin/env python3
"""Group unverified abstract candidates by publication and candidate string."""
import argparse
import csv
from pathlib import Path

FIELDS = ("openalex_id", "candidate_binomial", "mention_count",
          "feeding_keyword_windows", "negation_keyword_windows", "sample_context",
          "taxonomy_status", "feeding_evidence_status", "safety_status")


def group_mentions(rows):
    groups = {}
    for row in rows:
        identifier = (row.get("openalex_id") or "").strip()
        candidate = (row.get("candidate_binomial") or "").strip()
        if not identifier.startswith("https://openalex.org/W") or not candidate:
            continue
        key = (identifier, candidate.casefold())
        if key not in groups:
            groups[key] = dict(openalex_id=identifier, candidate_binomial=candidate,
                               mention_count=0, feeding_keyword_windows=0,
                               negation_keyword_windows=0, sample_context=row.get("context") or "",
                               taxonomy_status="unverified", feeding_evidence_status="unverified",
                               safety_status="not_assessed")
        record = groups[key]
        record["mention_count"] += 1
        for field, source in (("feeding_keyword_windows", "feeding_keyword_nearby"),
                              ("negation_keyword_windows", "negation_keyword_nearby")):
            if str(row.get(source, "")).strip().lower() in ("true", "1"):
                record[field] += 1
    return sorted(groups.values(), key=lambda x: (-x["feeding_keyword_windows"],
                    -x["mention_count"], x["candidate_binomial"].casefold(), x["openalex_id"]))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.input.resolve() == args.output.resolve():
        parser.error("input and output must differ")
    with args.input.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    required = {"openalex_id", "candidate_binomial", "context",
                "feeding_keyword_nearby", "negation_keyword_nearby"}
    if rows and not required.issubset(rows[0]):
        parser.error("input columns missing")
    output = group_mentions(rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(output)
    print(f"input_mentions={len(rows)} grouped_review_records={len(output)}")


if __name__ == "__main__":
    main()
