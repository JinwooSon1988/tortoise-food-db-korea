#!/usr/bin/env python3
"""Run end-to-end GBIF taxonomy import and render a searchable, unverified directory.

Example:
 python scripts/publish_bulk_taxonomy.py --input data/gbif_export.csv \
   --staged data/bulk_taxon_catalog.json \
   --html taxonomy/index.html --minimum 10000

This pipeline intentionally does NOT edit reviewed feeding data or assert food safety.
"""
import argparse
import json
from pathlib import Path

from build_bulk_taxon_catalog import read_rows, stage
from build_taxonomy_directory import build
from export_public_taxonomy_search import export

ROOT = Path(__file__).resolve().parents[1]


def execute(input_path, staged_path, html_path, plants_path, minimum=0, search_path=None):
    plants = json.loads(plants_path.read_text(encoding="utf-8"))
    rows = read_rows(input_path)
    staged, rejected = stage(rows, plants)
    if len(staged) < minimum:
        raise ValueError(
            f"Only {len(staged)} accepted non-duplicate taxa, below minimum {minimum}. "
            "No output published; obtain additional verified source records."
        )
    # Generate and validate HTML before touching output paths.
    markup = build(staged)
    search_data = export(staged)
    report = {
        "source_file": input_path.name,
        "existing_reviewed_records": len(plants),
        "source_rows": len(rows),
        "new_taxonomy_only_records": len(staged),
        "total_searchable_if_linked": len(plants) + len(staged),
        "feeding_verdicts_added": 0,
        "rejected": rejected,
        "warning": "Taxonomy-only entries have NOT been approved as tortoise food.",
    }
    output = {
        "schema_version": "1.0",
        "source_file": input_path.name,
        "records": staged,
        "summary": report,
    }
    staged_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.parent.mkdir(parents=True, exist_ok=True)
    staged_path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    html_path.write_text(markup, encoding="utf-8")
    if search_path is not None:
        search_path.parent.mkdir(parents=True, exist_ok=True)
        search_path.write_text(json.dumps(search_data, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    return report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--staged", type=Path, default=ROOT / "data/bulk_taxon_catalog.json")
    ap.add_argument("--html", type=Path, default=ROOT / "taxonomy/index.html")
    ap.add_argument("--plants", type=Path, default=ROOT / "data/plants.json")
    ap.add_argument("--minimum", type=int, default=0)
    ap.add_argument("--search", type=Path, help="Export to existing all-plants catalog search JSON")
    args = ap.parse_args()
    if args.minimum < 0:
        ap.error("--minimum must be nonnegative")
    result = execute(args.input, args.staged, args.html, args.plants, args.minimum, args.search)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
