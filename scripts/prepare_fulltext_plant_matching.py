#!/usr/bin/env python3
"""Convert collected PMC full texts to review-only inputs for exact plant matching."""
import argparse
import json
import tempfile
from pathlib import Path


def convert(fulltexts, output):
    if fulltexts.resolve() == output.resolve() or output.exists():
        raise ValueError("output must be new and distinct")
    seen = set()
    count = 0
    # Stream potentially million-character article bodies to disk; never retain
    # every fulltext in a Python list. Publish only after all rows validate.
    with tempfile.TemporaryDirectory(prefix=".fulltext-prep-") as scratch:
        spool_path = Path(scratch) / "prepared.jsonl"
        with fulltexts.open(encoding="utf-8") as source_stream, spool_path.open(
                "w", encoding="utf-8") as spool:
            for line_no, line in enumerate(source_stream, 1):
                if not line.strip():
                    continue
                record = json.loads(line)
                if record.get("review_status") != "unverified_fulltext_for_manual_review" or record.get("feeding_verdict") is not None:
                    raise ValueError(f"invalid review-only fulltext at line {line_no}")
                source = record.get("source_database")
                identifier = record.get("source_record_id")
                body = record.get("fulltext_excerpt")
                if not source or not identifier or not isinstance(body, str) or not body.strip():
                    raise ValueError(f"missing fulltext provenance at line {line_no}")
                key = (source, identifier)
                if key in seen:
                    raise ValueError(f"duplicate fulltext at line {line_no}")
                seen.add(key)
                row = {"source_database": source, "source_record_id": identifier,
                       "source_url": record.get("source_url"), "title": record.get("source_title"),
                       "abstract_text": body, "review_status": "unmatched_literature_lead",
                       "feeding_verdict": None}
                spool.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
                count += 1
        if not count:
            raise ValueError("no fulltexts for matching")
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("x", encoding="utf-8") as destination, spool_path.open(
                encoding="utf-8") as source_stream:
            for chunk in iter(lambda: source_stream.read(1024 * 1024), ""):
                destination.write(chunk)
    return {"fulltexts_prepared": count, "status": "unverified_review_only"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("fulltexts", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(convert(args.fulltexts, args.output), sort_keys=True))
