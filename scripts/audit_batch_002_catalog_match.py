#!/usr/bin/env python3
"""Audit exact Batch 002 species-name matches against all 40 catalog shards.

Does not infer feeding safety, synonymy, or suitability.
"""
import collections
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BATCH = ROOT / "data/catalog-evidence/batch-002-20261021.json"
SHARDS = ROOT / "data/plant-catalog"

def main():
    batch = json.loads(BATCH.read_text(encoding="utf-8"))
    catalog = collections.defaultdict(list)
    shard_paths = sorted(SHARDS.glob("taxa-??.json"))
    if len(shard_paths) != 40:
        raise SystemExit(f"Expected 40 catalog shards, found {len(shard_paths)}")
    for path in shard_paths:
        for plant in json.loads(path.read_text(encoding="utf-8"))["records"]:
            catalog[plant["scientific"].strip().casefold()].append(plant["id"])
    names = collections.defaultdict(list)
    for record in batch["records"]:
        names[record["reported_name"].strip().casefold()].append(record)
    matched = {name: catalog[name] for name in names if name in catalog}
    unmatched = sorted(set(names) - set(matched))
    result = {
        "batch": batch["batch"],
        "catalog_shards": len(shard_paths),
        "catalog_distinct_names": len(catalog),
        "batch_records": len(batch["records"]),
        "batch_distinct_reported_names": len(names),
        "exact_matched_species_names": len(matched),
        "exact_matched_records": sum(len(names[n]) for n in matched),
        "unmatched_species_names": len(unmatched),
        "unmatched_names": unmatched,
        "ambiguous_exact_matches": {n: ids for n, ids in matched.items() if len(ids) > 1},
        "note": "Exact name matching only; unmatched names require taxonomic review, not inferred synonyms. No safety grades are assigned."
    }
    out = ROOT / "data/catalog-evidence/batch-002-match-audit.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k not in ("unmatched_names","ambiguous_exact_matches")}, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
