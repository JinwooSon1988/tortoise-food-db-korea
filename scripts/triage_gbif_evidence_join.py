#!/usr/bin/env python3
"""Build a review queue from a GBIF-to-evidence join, without making feeding claims.

Usage: python scripts/triage_gbif_evidence_join.py path/to/gbif_candidate_evidence_join.json
Produces CSV summaries for expert verification. Does not alter site data.
"""
import argparse
import csv
import json
from collections import Counter
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("join_json", type=Path)
    parser.add_argument("--outdir", type=Path, default=Path("research/generated/triage"))
    args = parser.parse_args()
    data = json.loads(args.join_json.read_text(encoding="utf-8"))
    rows = data["rows"]
    args.outdir.mkdir(parents=True, exist_ok=True)
    # Leads are unverified and never qualify as a feeding verdict.
    queue = sorted(rows, key=lambda r: (0 if r.get("evidence_lead_ids") else 1,
                                         r.get("family") or "", r.get("scientific") or ""))
    columns = ["gbif_taxon_key", "scientific", "family", "status",
               "gbif_url", "evidence_lead_ids", "evidence_lead_urls",
               "review_required", "feeding_verdict", "site_publishable"]
    with (args.outdir / "candidate_review_queue.csv").open("w", newline="", encoding="utf-8-sig") as fp:
        writer = csv.DictWriter(fp, fieldnames=columns)
        writer.writeheader()
        for row in queue:
            writer.writerow({
                "gbif_taxon_key": row.get("gbif_taxon_key"),
                "scientific": row.get("scientific"),
                "family": row.get("family"),
                "status": row.get("status"),
                "gbif_url": row.get("gbif_url"),
                "evidence_lead_ids": "; ".join(row.get("evidence_lead_ids", [])),
                "evidence_lead_urls": "; ".join(row.get("evidence_lead_urls", [])),
                "review_required": "original_source|tortoise_taxon|plant_part|directness|limitations",
                "feeding_verdict": "",
                "site_publishable": "false",
            })
    counts = Counter(r.get("family") or "unknown" for r in rows)
    with (args.outdir / "family_coverage.csv").open("w", newline="", encoding="utf-8-sig") as fp:
        writer = csv.writer(fp)
        writer.writerow(["family", "candidate_count"])
        writer.writerows(counts.most_common())
    catalog = data.get("existing_catalog_evidence", [])
    with (args.outdir / "existing_catalog_evidence.csv").open("w", newline="", encoding="utf-8-sig") as fp:
        writer = csv.writer(fp)
        writer.writerow(["plant_id", "scientific", "evidence_ids", "source_urls"])
        for item in catalog:
            writer.writerow([item.get("plant_id"), item.get("scientific"),
                             "; ".join(item.get("evidence_ids", [])),
                             "; ".join(u for u in item.get("source_urls", []) if u)])
    print(json.dumps({"candidates": len(rows), "lead_candidates": sum(bool(r.get("evidence_lead_ids")) for r in rows),
                      "catalog_plants": len(catalog), "families": len(counts),
                      "output_dir": str(args.outdir)}, ensure_ascii=False))
if __name__ == "__main__":
    main()
