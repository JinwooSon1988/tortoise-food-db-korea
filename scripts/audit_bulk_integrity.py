#!/usr/bin/env python3
"""Read-only, deterministic integrity audit for large tortoise plant/evidence datasets.

Usage: python scripts/audit_bulk_integrity.py [--root .] [--output bulk-audit.json]
No automatic safety verdicts are generated. Exit 1 on integrity errors.
"""
import argparse
import json
import os
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def load(path):
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def rows(data, key=None):
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and key and isinstance(data.get(key), list):
        return data[key]
    raise ValueError("Expected list or object with list at " + str(key))


def audit(root):
    data = root / "data"
    paths = {
        "plants": data / "plants.json",
        "assessments": data / "public_assessments.json",
        "evidence": data / "public_evidence_records.json",
    }
    with ThreadPoolExecutor(max_workers=min(3, os.cpu_count() or 1)) as pool:
        futures = {key: pool.submit(load, path) for key, path in paths.items()}
        loaded = {key: future.result() for key, future in futures.items()}
    plants = rows(loaded["plants"])
    assessments = rows(loaded["assessments"])
    evidence = rows(loaded["evidence"], "records")
    errors = []
    warnings = []

    def unique(items, field, name):
        values = [item.get(field) for item in items]
        for value, count in sorted(Counter(str(v) for v in values if v is not None).items()):
            if count > 1:
                errors.append({"code": "duplicate_id", "dataset": name, "value": value, "count": count})
        for index, value in enumerate(values):
            if not isinstance(value, str) or not value.strip():
                errors.append({"code": "missing_id", "dataset": name, "index": index})
        return {v for v in values if isinstance(v, str) and v.strip()}

    plant_ids = unique(plants, "id", "plants")
    evidence_ids = unique(evidence, "id", "evidence")
    for record in evidence:
        eid = record.get("id")
        for pid in record.get("plant_ids", []):
            if pid not in plant_ids:
                errors.append({"code": "unknown_evidence_plant", "evidence_id": eid, "plant_id": pid})
        if not record.get("source_title") or not (record.get("url") or record.get("doi") or record.get("pmid")):
            warnings.append({"code": "incomplete_citation", "evidence_id": eid})

    keys = Counter()
    for record in assessments:
        pid = record.get("plant_id")
        group = record.get("species_group", "")
        keys[(str(pid), str(group))] += 1
        if pid not in plant_ids:
            errors.append({"code": "unknown_assessment_plant", "plant_id": pid})
        for eid in record.get("evidence_ids", []):
            if eid not in evidence_ids:
                errors.append({"code": "unknown_assessment_evidence", "plant_id": pid, "evidence_id": eid})
        if record.get("verdict") in ("supported_mixed_diet", "limited_mixed_diet") and not record.get("evidence_ids"):
            errors.append({"code": "positive_verdict_without_evidence", "plant_id": pid})
    for (pid, group), count in sorted(keys.items()):
        if count > 1:
            errors.append({"code": "duplicate_assessment", "plant_id": pid, "species_group": group, "count": count})

    return {
        "schema_version": 1,
        "counts": {"plants": len(plants), "assessments": len(assessments), "evidence": len(evidence)},
        "passed": not errors,
        "errors": sorted(errors, key=lambda x: json.dumps(x, ensure_ascii=False, sort_keys=True)),
        "warnings": sorted(warnings, key=lambda x: json.dumps(x, ensure_ascii=False, sort_keys=True)),
        "note": "Integrity only; does not verify source accuracy, taxonomic identity, or feeding safety.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = audit(args.root)
    result = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(result, encoding="utf-8")
    else:
        print(result, end="")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
