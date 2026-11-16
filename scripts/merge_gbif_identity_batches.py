#!/usr/bin/env python3
"""Fail-closed cross-batch deduplication of review-only GBIF identity candidates."""
import argparse
import json
import os
import tempfile
import unicodedata
from pathlib import Path


def merge(inputs, output, report):
    if not inputs or len({p.resolve() for p in inputs}) != len(inputs):
        raise ValueError("unique input paths required")
    if len({p.resolve() for p in [*inputs, output, report]}) != len(inputs) + 2:
        raise ValueError("output/report paths must be distinct from inputs")
    if output.exists() or report.exists():
        raise FileExistsError("refusing to overwrite prior results")
    seen = {}
    names = {}
    counts = {"read": 0, "unique": 0, "duplicate": 0, "conflicts": 0}
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".gbif-merge-", dir=output.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as dest:
            for path in inputs:
                with path.open(encoding="utf-8") as src:
                    for number, line in enumerate(src, 1):
                        if not line.strip():
                            continue
                        counts["read"] += 1
                        row = json.loads(line)
                        if row.get("feed_review_status") != "identity_only" or row.get("reconciliation_status") != "pending":
                            raise ValueError(f"{path}:{number}: non-review candidate")
                        if row.get("source_id") != "GBIF" or not str(row.get("source_record_id") or "").isdigit():
                            raise ValueError(f"{path}:{number}: invalid GBIF source identity")
                        if any(key in row for key in ("safe", "verdict", "feeding_verdict", "feed_assessment")):
                            raise ValueError(f"{path}:{number}: feeding claim prohibited")
                        key = (row["source_id"], str(row["source_record_id"]))
                        identity = (row.get("canonical_scientific_name"), row.get("taxonomic_status"),
                                    row.get("source_url"), row.get("family"))
                        if not identity[0] or identity[1] != "accepted" or identity[2] != f"https://www.gbif.org/species/{key[1]}":
                            raise ValueError(f"{path}:{number}: inconsistent GBIF identity")
                        if key in seen:
                            if seen[key] != identity:
                                counts["conflicts"] += 1
                                raise ValueError(f"{path}:{number}: conflicting GBIF record {key}")
                            counts["duplicate"] += 1
                            continue
                        seen[key] = identity
                        canonical = unicodedata.normalize('NFKC', identity[0]).casefold().strip()
                        names.setdefault(canonical, []).append(key[1])
                        dest.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
                        counts["unique"] += 1
        collisions = {name: ids for name, ids in names.items() if len(ids) > 1}
        counts["canonical_name_collision_groups"] = len(collisions)
        counts["canonical_name_collision_records"] = sum(len(ids) for ids in collisions.values())
        counts["distinct_canonical_names"] = len(names)
        if not counts["unique"]:
            raise ValueError("zero candidates: refusing empty merge")
        # Write report before publishing merged data; fail closed on errors.
        report.parent.mkdir(parents=True, exist_ok=True)
        fd_report, tmp_report = tempfile.mkstemp(prefix=".gbif-report-", dir=report.parent)
        try:
            with os.fdopen(fd_report, "w", encoding="utf-8") as target:
                json.dump({"counts": counts, "input_files": len(inputs), "status": "identity_only",
                           "canonical_name_collisions": [{"name": name, "gbif_keys": ids} for name, ids in sorted(collisions.items())],
                           "name_collision_policy": "flag for taxonomic review; never merge distinct GBIF keys automatically",
                           "note": "Taxonomic identity only; not feeding safety evidence"}, target, indent=2)
                target.write("\n")
            os.replace(temporary, output)
            os.replace(tmp_report, report)
        finally:
            if os.path.exists(tmp_report):
                os.unlink(tmp_report)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return counts


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(merge(args.inputs, args.output, args.report), sort_keys=True))


if __name__ == "__main__":
    main()
