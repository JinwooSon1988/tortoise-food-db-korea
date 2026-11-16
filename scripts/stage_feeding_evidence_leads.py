#!/usr/bin/env python3
"""Validate batches of literature/feeding leads without inferring feeding safety.

Rows are *leads* for human review, never published feeding assessments.
"""
import argparse
import json
import os
import tempfile
from collections import Counter
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

KINDS = {"peer_reviewed", "veterinary", "zoo_husbandry", "government", "community", "other"}
FORBIDDEN = {"safe", "verdict", "feeding_verdict", "feed_assessment", "recommended", "toxic"}


def validate(row):
    if not isinstance(row, dict) or FORBIDDEN.intersection(row):
        raise ValueError("object required; feeding verdicts prohibited")
    required = ("plant_scientific_name", "source_url", "source_type", "source_title", "observed_at")
    if any(not isinstance(row.get(k), str) or not row[k].strip() for k in required):
        raise ValueError("missing required provenance fields")
    if row["source_type"] not in KINDS:
        raise ValueError("unsupported source_type")
    parsed = urlsplit(row["source_url"])
    if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
        raise ValueError("source_url must be an HTTPS URL without credentials")
    try:
        if date.fromisoformat(row["observed_at"]).isoformat() != row["observed_at"]:
            raise ValueError("invalid observed_at")
    except ValueError as exc:
        raise ValueError("invalid observed_at") from exc
    for optional in ("plant_part", "tortoise_scientific_name", "source_identifier"):
        if optional in row and row[optional] is not None and not isinstance(row[optional], str):
            raise ValueError(f"invalid {optional}")
    # No default species or plant part: absence must remain explicit.
    return {
        "plant_scientific_name": row["plant_scientific_name"].strip(),
        "plant_part": (row.get("plant_part") or "").strip() or None,
        "tortoise_scientific_name": (row.get("tortoise_scientific_name") or "").strip() or None,
        "source_type": row["source_type"],
        "source_title": row["source_title"].strip(),
        "source_url": row["source_url"],
        "source_identifier": (row.get("source_identifier") or "").strip() or None,
        "observed_at": row["observed_at"],
        "review_status": "unverified_lead",
        "feeding_verdict": None,
    }


def process(inputs, output, report):
    paths = [*inputs, output, report]
    if not inputs or len({p.resolve() for p in paths}) != len(paths):
        raise ValueError("all input and output paths must be distinct")
    if output.exists() or report.exists():
        raise FileExistsError("existing output must not be overwritten")
    counts = Counter()
    seen = set()
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".evidence-leads-", dir=output.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as target:
            for source in inputs:
                with source.open(encoding="utf-8") as stream:
                    for number, line in enumerate(stream, 1):
                        if not line.strip():
                            continue
                        counts["read"] += 1
                        try:
                            item = validate(json.loads(line))
                        except (ValueError, TypeError, json.JSONDecodeError) as exc:
                            raise ValueError(f"{source}:{number}: {exc}") from exc
                        key = (item["plant_scientific_name"].casefold(), item["plant_part"],
                               item["tortoise_scientific_name"], item["source_url"], item["source_identifier"])
                        if key in seen:
                            counts["duplicate"] += 1
                            continue
                        seen.add(key)
                        target.write(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n")
                        counts["leads"] += 1
        if not counts["leads"]:
            raise ValueError("empty leads: refusing to publish")
        report.parent.mkdir(parents=True, exist_ok=True)
        fd2, temporary_report = tempfile.mkstemp(prefix=".evidence-report-", dir=report.parent)
        try:
            with os.fdopen(fd2, "w", encoding="utf-8") as stream:
                json.dump({"counts": dict(counts), "status": "unverified_leads_only",
                           "note": "Not feeding assessments; taxon, plant part and tortoise species require review."},
                          stream, indent=2)
                stream.write("\n")
            os.replace(temporary, output)
            os.replace(temporary_report, report)
        finally:
            if os.path.exists(temporary_report):
                os.unlink(temporary_report)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return dict(counts)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("inputs", type=Path, nargs="+")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(process(args.inputs, args.output, args.report), sort_keys=True))
