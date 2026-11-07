#!/usr/bin/env python3
"""Audit source-context reviews against the complete source-first queue.

Context verification is not plant-association verification or feeding safety.
Read-only; fail closed if counts or safety boundaries drift.
"""
import argparse
import json
from pathlib import Path

def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def audit(queue, reviews):
    sources = {r["source_url"]: r for r in queue["records"]}
    errors = []
    seen = set()
    checked_links = 0
    for review in reviews["records"]:
        url = review["url"]
        if url in seen:
            errors.append("duplicate reviewed source: " + url)
        seen.add(url)
        item = sources.get(url)
        if item is None:
            errors.append("review source missing from queue: " + url)
            continue
        pending = len(item["taxon_associations"])
        checked_links += pending
        if review.get("plant_associations_pending") != pending:
            errors.append("pending link count mismatch: " + url)
        if review.get("plant_associations_verified") != 0:
            errors.append("unsubstantiated plant association promotion: " + url)
        if review.get("feeding_safety_status") != "unassessed":
            errors.append("unsubstantiated feeding safety promotion: " + url)
        if review.get("review_level") != "published_full_text_context_reviewed":
            errors.append("unknown review level: " + url)
        for key in ("species", "method", "source", "finding", "limit"):
            if not review.get(key):
                errors.append("missing context field " + key + ": " + url)
    return {"status": "fail" if errors else "pass",
            "reviewed_sources": len(seen), "candidate_links_pending": checked_links,
            "errors": errors}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--queue", default="data/research_unique_source_review_queue.json")
    p.add_argument("--reviews", default="data/research_source_context_reviews_20261104.json")
    args = p.parse_args()
    result = audit(read(args.queue), read(args.reviews))
    print(json.dumps(result, ensure_ascii=False))
    if result["errors"]:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
