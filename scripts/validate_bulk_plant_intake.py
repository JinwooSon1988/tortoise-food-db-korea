#!/usr/bin/env python3
"""Validate a large, evidence-first plant intake batch without publishing it."""
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))
def check(rows, existing):
    errors = []
    seen = set()
    if not isinstance(rows, list):
        return ["Batch must be a JSON array"]
    for n, row in enumerate(rows, 1):
        tag = f"row {n}"
        if not isinstance(row, dict):
            errors.append(f"{tag}: expected object"); continue
        pid = row.get("id")
        if not isinstance(pid, str) or not re.fullmatch(r"[a-z0-9]+(?:_[a-z0-9]+)*", pid):
            errors.append(f"{tag}: invalid stable plant ID"); continue
        if pid in existing or pid in seen:
            errors.append(f"{tag}: duplicate/existing ID {pid}")
        seen.add(pid)
        for field in ("ko", "en", "scientific", "family"):
            if not isinstance(row.get(field), str) or not row[field].strip():
                errors.append(f"{tag}: missing {field}")
        sources = row.get("sources")
        if not isinstance(sources, list) or not sources:
            errors.append(f"{tag}: at least one traceable source required")
            sources = []
        for j, source in enumerate(sources, 1):
            if not isinstance(source, dict) or not all(isinstance(source.get(k), str) and source[k].strip() for k in ("title", "url", "source_type", "claim", "plant_part", "animal_taxon", "limitations")):
                errors.append(f"{tag}: source {j} missing provenance/scope fields")
            elif not source["url"].startswith(("https://", "http://")):
                errors.append(f"{tag}: source {j} invalid URL")
        state = row.get("publication_status")
        if state not in ("research_only", "review_required"):
            errors.append(f"{tag}: new plants must remain research_only/review_required")
        if row.get("feeding_verdict") not in (None, "unassessed"):
            errors.append(f"{tag}: feeding verdict requires separate reviewed assessment")
        if row.get("nutrition_status") not in ("not_linked", "reference_only", "verified"):
            errors.append(f"{tag}: nutrition status must be explicit")
        if row.get("nutrition_status") == "verified" and not row.get("nutrition_source_url"):
            errors.append(f"{tag}: verified nutrition requires source URL")
    return errors

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("batch", help="JSON file of researched candidate plants")
    args = parser.parse_args()
    existing = {p["id"] for p in load(ROOT / "data/plants.json")}
    rows = load(args.batch)
    errors = check(rows, existing)
    for err in errors: print("ERROR:", err)
    if errors: raise SystemExit(1)
    print(f"PASS: {len(rows)} new candidate records; none published or graded")
if __name__ == "__main__":
    main()
