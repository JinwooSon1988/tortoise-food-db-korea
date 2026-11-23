#!/usr/bin/env python3
"""Bounded concurrent GBIF checks of unverified binomial strings.

EXACT matches to Plantae only; never infer feeding or safety from taxonomy.
"""
import argparse
import concurrent.futures
import csv
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://api.gbif.org/v1/species/match"


def resolve(name, timeout=15, retries=2):
    url = API + "?" + urllib.parse.urlencode({"name": name, "kingdom": "Plantae", "strict": "true"})
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(urllib.request.Request(
                url, headers={"User-Agent": "GeobukbapResearch/1.0 taxonomy-only"}),
                timeout=timeout) as response:
                return json.load(response)
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            if attempt == retries:
                return {"error": type(exc).__name__}
            time.sleep(min(2 ** attempt, 4))


def classify(name, result):
    if "error" in result:
        return "lookup_failed"
    if result.get("matchType") != "EXACT":
        return "not_exact_plant_match"
    if result.get("kingdom") != "Plantae":
        return "not_exact_plant_match"
    if result.get("rank") not in ("SPECIES", "SUBSPECIES", "VARIETY", "FORM"):
        return "not_exact_plant_match"
    canonical = result.get("canonicalName", "").casefold().strip()
    if canonical != name.casefold().strip():
        return "not_exact_plant_match"
    if result.get("status") == "DOUBTFUL":
        return "ambiguous_plant_match"
    return "exact_plant_taxon_candidate"


def process(rows, workers=6, resolver=resolve):
    names = sorted({r["candidate_binomial"].strip() for r in rows if r.get("candidate_binomial", "").strip()})
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        results = dict(zip(names, pool.map(resolver, names)))
    output = []
    for row in rows:
        name = row.get("candidate_binomial", "").strip()
        match = results.get(name, {})
        output.append({
            **row,
            "gbif_status": classify(name, match),
            "gbif_taxon_key": match.get("usageKey", ""),
            "gbif_scientific_name": match.get("scientificName", ""),
            "gbif_match_type": match.get("matchType", ""),
            "taxonomy_review_status": "unreviewed",
            "feeding_evidence_status": "unverified",
            "safety_verdict": "not_assessed",
        })
    return output


def main():
    p = argparse.ArgumentParser()
    p.add_argument("input", type=Path)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--workers", type=int, default=6)
    args = p.parse_args()
    if not 1 <= args.workers <= 12:
        p.error("workers must be between 1 and 12")
    if args.input.resolve() == args.output.resolve():
        p.error("input and output must differ")
    with args.input.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows or "candidate_binomial" not in rows[0]:
        p.error("input requires candidate_binomial column and rows")
    output = process(rows, workers=args.workers)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(output[0]))
        writer.writeheader()
        writer.writerows(output)
    counts = {}
    for row in output:
        status = row["gbif_status"]
        counts[status] = counts.get(status, 0) + 1
    print(json.dumps({"records": len(output), "unique_strings": len({x["candidate_binomial"] for x in output}), "statuses": counts, "confirmed_feeding": 0, "safety_verdicts": 0}))


if __name__ == "__main__":
    main()
