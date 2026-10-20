#!/usr/bin/env python3
"""Stage large plant-taxonomy catalogs without asserting tortoise food safety.

Usage:
 python scripts/build_bulk_taxon_catalog.py --input path/to/gbif.csv --output data/bulk_taxon_catalog.json
 python scripts/build_bulk_taxon_catalog.py --input path/to/gbif.json --output data/bulk_taxon_catalog.json

Input columns: scientificName (or scientific), taxonRank, taxonomicStatus,
acceptedScientificName, family, kingdom, gbifID/key, sourceUrl, datasetKey.
Only accepted species or infraspecific taxa with traceable taxon identifiers
are eligible. Existing plants and duplicate accepted names are excluded.
"""
import argparse
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BINOMIAL = re.compile(r"^[A-Z][a-z-]+ [a-z][a-z-]+(?: (?:subsp\.|ssp\.|var\.) [a-z][a-z-]+)?$")
RANKS = {"species", "subspecies", "variety"}
ACCEPTED = {"accepted", "valid"}
PLANT_KINGDOM = {"plantae"}

def norm(value):
    return " ".join(str(value or "").strip().split()).casefold()

def get(row, *names):
    for name in names:
        value = row.get(name)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""

def read_rows(path):
    if path.suffix.lower() == ".csv":
        with path.open(encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f))
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    for key in ("records", "candidates", "results", "taxa"):
        if isinstance(data.get(key), list):
            return data[key]
    raise ValueError("Expected a JSON list or records/candidates/results/taxa list")

def stage(rows, existing):
    existing_names = {norm(p.get("scientific")) for p in existing}
    used_names = set()
    accepted_rows = []
    rejected = {}
    def reject(reason):
        rejected[reason] = rejected.get(reason, 0) + 1
    for row in rows:
        if not isinstance(row, dict):
            reject("not_object"); continue
        name = get(row, "acceptedScientificName", "accepted_scientific_name", "scientificName", "scientific")
        rank = norm(get(row, "taxonRank", "rank"))
        status = norm(get(row, "taxonomicStatus", "status"))
        kingdom = norm(get(row, "kingdom"))
        taxon_id = get(row, "gbifID", "taxonKey", "key", "taxon_id", "id")
        source_url = get(row, "sourceUrl", "source_url", "taxon_url")
        if not name or not BINOMIAL.fullmatch(name):
            reject("unresolved_scientific_name"); continue
        if rank not in RANKS:
            reject("not_species_rank"); continue
        if status not in ACCEPTED:
            reject("not_accepted_taxon"); continue
        if kingdom not in PLANT_KINGDOM:
            reject("not_verified_plantae"); continue
        if not taxon_id or not (source_url or get(row, "datasetKey", "dataset_key")):
            reject("missing_traceable_taxon_source"); continue
        key = norm(name)
        if key in existing_names:
            reject("already_in_public_catalog"); continue
        if key in used_names:
            reject("duplicate_taxon"); continue
        used_names.add(key)
        accepted_rows.append({
            "scientific": name,
            "family": get(row, "family") or None,
            "rank": rank,
            "taxon_id": taxon_id,
            "taxonomy_source_url": source_url or None,
            "taxonomy_dataset_key": get(row, "datasetKey", "dataset_key") or None,
            "feeding_status": "unverified",
            "feeding_grade": None,
            "feeding_evidence_ids": [],
            "identity_status": "taxonomy_source_recorded",
            "publication_status": "staged_not_public",
        })
    accepted_rows.sort(key=lambda x: x["scientific"].casefold())
    return accepted_rows, rejected

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--plants", type=Path, default=ROOT / "data/plants.json")
    args = ap.parse_args()
    existing = json.loads(args.plants.read_text(encoding="utf-8"))
    rows = read_rows(args.input)
    staged, rejected = stage(rows, existing)
    payload = {
        "schema_version": "1.0",
        "source_file": args.input.name,
        "existing_public_plants": len(existing),
        "input_rows": len(rows),
        "new_taxonomy_candidates": len(staged),
        "rejected_counts": rejected,
        "warning": "Staged taxonomy only; not feeding evidence, not a public catalog, not safe-to-feed.",
        "records": staged,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in payload.items() if k != "records"}, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
