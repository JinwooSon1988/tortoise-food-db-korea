#!/usr/bin/env python3
"""Stream large plant candidate feeds into review-only NDJSON, never feeding verdicts.

Usage: python scripts/stage_plant_bulk_stream.py input.jsonl --output staged.jsonl --report report.json
Input rows must have scientific_name (or canonical_scientific_name), source_id,
source_url, observed_at. Output remains identity_only and is never published.
"""
import argparse
import json
import re
import unicodedata
from collections import Counter
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit


def clean(value):
    if not isinstance(value, str):
        return ""
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", value)).strip()


def normalize(row):
    if not isinstance(row, dict):
        raise ValueError("row must be an object")
    forbidden = {"verdict", "safe", "feeding_verdict", "feed_assessment"}
    if forbidden.intersection(row):
        raise ValueError("feeding safety claims are forbidden in identity staging")
    name = clean(row.get("canonical_scientific_name") or row.get("scientific_name"))
    source = clean(row.get("source_id"))
    url = clean(row.get("source_url"))
    observed = clean(row.get("observed_at"))
    source_record = clean(row.get("source_record_id"))
    if not all((name, source, url, observed)):
        raise ValueError("scientific name, source_id, source_url and observed_at are required")
    parsed = urlsplit(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError("source_url must be an absolute HTTP(S) URL")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", observed):
        raise ValueError("observed_at must be YYYY-MM-DD")
    try:
        date.fromisoformat(observed)
    except ValueError as exc:
        raise ValueError("observed_at is not a valid calendar date") from exc
    status = clean(row.get("taxonomic_status")) or "unresolved"
    if status not in {"accepted", "synonym", "unplaced", "unresolved"}:
        raise ValueError("unsupported taxonomic_status")
    # The same source record must never be silently assigned conflicting taxon names.
    key = (source.casefold(), (source_record or name).casefold())
    return key, {
        "candidate_id": source.casefold() + ":" + (source_record or name).casefold(),
        "canonical_scientific_name": name,
        "family": clean(row.get("family")) or None,
        "taxonomic_status": status,
        "source_id": source,
        "source_url": url,
        "source_record_id": source_record or None,
        "observed_at": observed,
        "reconciliation_status": "pending",
        "feed_review_status": "identity_only",
    }


def stage(input_path, output_path, report_path):
    resolved = [input_path.resolve(), output_path.resolve(), report_path.resolve()]
    if len(set(resolved)) != 3:
        raise ValueError("input, output and report must be distinct files")
    seen = {}
    counts = Counter()
    errors = []
    # A temporary output avoids publishing a partial staging file on validation failure.
    temporary = output_path.with_name(output_path.name + ".tmp")
    if temporary.resolve() in resolved:
        raise ValueError("temporary output conflicts with input or report")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with input_path.open(encoding="utf-8") as source, temporary.open("w", encoding="utf-8") as target:
            for line_number, line in enumerate(source, 1):
                if not line.strip():
                    continue
                counts["read"] += 1
                try:
                    key, item = normalize(json.loads(line))
                    prior = seen.get(key)
                    if prior is not None:
                        if prior != (item["canonical_scientific_name"].casefold(), item["source_url"], item["taxonomic_status"]):
                            raise ValueError("conflicting identity, URL or taxonomic status for same source record")
                        counts["duplicates"] += 1
                        continue
                    seen[key] = (item["canonical_scientific_name"].casefold(), item["source_url"], item["taxonomic_status"])
                    target.write(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n")
                    counts["staged"] += 1
                except (ValueError, TypeError, json.JSONDecodeError) as exc:
                    counts["rejected"] += 1
                    if len(errors) < 100:
                        errors.append({"line": line_number, "reason": str(exc)})
        if counts["rejected"]:
            temporary.unlink(missing_ok=True)
        else:
            temporary.replace(output_path)
    finally:
        temporary.unlink(missing_ok=True)
    report = {
        "schema_version": 1, "counts": dict(sorted(counts.items())),
        "passed": counts["rejected"] == 0,
        "errors": errors,
        "note": "Taxonomic identity candidates only; no tortoise feeding-safety inference.",
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    result = stage(args.input, args.output, args.report)
    print(json.dumps(result["counts"], sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
