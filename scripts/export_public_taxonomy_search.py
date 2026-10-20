#!/usr/bin/env python3
"""Export accepted taxonomy-only records into the EXISTING all-plants search format.

Usage:
 python scripts/export_public_taxonomy_search.py \
   --input data/bulk_taxon_catalog.json \
   --output data/plant-catalog/search.json

This is a data export only. It does not claim the taxonomy is tortoise food.
Existing all-plants UI reads rows as:
 [taxon_id, scientific_name, family, English_name, Korean_name, evidence_flag].
"""
import argparse
import json
from pathlib import Path


def export(records):
    result = []
    ids, names = set(), set()
    for r in records:
        if r.get("feeding_status") != "unverified" or r.get("feeding_grade") is not None:
            raise ValueError("Unverified taxonomy-only input required")
        if r.get("publication_status") != "staged_not_public":
            raise ValueError("Input must originate from staged taxonomy")
        ident = str(r.get("taxon_id") or "").strip()
        scientific = str(r.get("scientific") or "").strip()
        if not ident or not scientific:
            raise ValueError("Taxonomy identity missing")
        if ident in ids or scientific.casefold() in names:
            raise ValueError("Duplicate taxonomy identity")
        ids.add(ident)
        names.add(scientific.casefold())
        result.append([ident, scientific, r.get("family") or "", "", "", False])
    return {"schema_version": "1.0", "rows": result}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raw = json.loads(args.input.read_text(encoding="utf-8"))
    records = raw["records"] if isinstance(raw, dict) else raw
    result = export(records)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"Exported {len(result['rows'])} unverified taxa to {args.output}")


if __name__ == "__main__":
    main()
