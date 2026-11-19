#!/usr/bin/env python3
"""Batch research-only botanical mentions across abstracts and optional PMC full texts.

All matching outputs remain unverified; this command never publishes feeding verdicts.
"""
import argparse
import concurrent.futures
import json
from pathlib import Path

try:
    from scripts.export_site_plant_binomials import export
    from scripts.build_research_taxonomy_index import build
    from scripts.audit_research_taxonomy_provenance import audit
    from scripts.link_plant_abstract_mentions import link
except ModuleNotFoundError:
    from export_site_plant_binomials import export
    from build_research_taxonomy_index import build
    from audit_research_taxonomy_provenance import audit
    from link_plant_abstract_mentions import link


def run(catalog, accepted, abstracts, fulltexts, output_dir):
    inputs = [catalog, accepted, abstracts] + ([fulltexts] if fulltexts else [])
    if len({p.resolve() for p in inputs}) != len(inputs):
        raise ValueError("inputs must be distinct")
    if output_dir.exists():
        raise ValueError("output directory must be new (no overwrites)")
    if any(output_dir.resolve() == p.resolve() or output_dir.resolve() in p.resolve().parents
           for p in inputs):
        raise ValueError("output directory cannot contain an input")
    # Validate every external source before writing any research artifacts.
    for path in inputs:
        if not path.is_file():
            raise FileNotFoundError(path)
    output_dir.mkdir(parents=True)
    site = output_dir / "site-binomial-taxonomy.csv"
    taxonomy = output_dir / "research-binomial-taxonomy.csv"
    export(catalog, site)
    taxonomy_counts = build(site, accepted, taxonomy, output_dir / "taxonomy-report.json")
    provenance_counts = audit(accepted, output_dir / "accepted-name-provenance.csv",
                              output_dir / "accepted-name-provenance-report.json")
    # Abstract and full-text corpora are independent: scan them concurrently.
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        abstract_future = pool.submit(
            link, abstracts, taxonomy, output_dir / "abstract-mentions.jsonl",
            output_dir / "abstract-report.json")
        fulltext_future = None
        if fulltexts:
            fulltext_future = pool.submit(
                link, fulltexts, taxonomy, output_dir / "fulltext-mentions.jsonl",
                output_dir / "fulltext-report.json", source_scope="fulltext")
        abstract_counts = abstract_future.result()
        fulltext_counts = fulltext_future.result() if fulltext_future else None
    report = {"taxonomy": taxonomy_counts, "provenance": provenance_counts,
              "abstracts": abstract_counts,
              "fulltexts": fulltext_counts, "status": "research_only_unverified_mentions",
              "feeding_verdict": None}
    (output_dir / "batch-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=Path, required=True,
                        help="Existing data/plants.json")
    parser.add_argument("--accepted", type=Path, required=True,
                        help="Accepted botanical names CSV with source references")
    parser.add_argument("--abstracts", type=Path, required=True,
                        help="Research-only literature JSONL")
    parser.add_argument("--fulltexts", type=Path,
                        help="Optional prepared PMC full-text matching JSONL")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.catalog, args.accepted, args.abstracts,
                         args.fulltexts, args.output_dir), sort_keys=True))
