#!/usr/bin/env python3
"""Fetch worldwide botanical taxa from GBIF; never infer feeding safety."""
import argparse
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = "https://api.gbif.org/v1/species/search"
VASCULAR_PLANTS_KEY = 7707728
def fetch_page(offset, limit, attempts=4):
    query = urllib.parse.urlencode({
        "rank": "SPECIES", "highertaxon_key": VASCULAR_PLANTS_KEY,
        "status": "ACCEPTED", "limit": limit, "offset": offset
    })
    req = urllib.request.Request(API + "?" + query,
        headers={"User-Agent": "GeobukbapResearch/1.0 (taxonomy-only)", "Accept": "application/json"})
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(req, timeout=45) as response:
                return json.load(response)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            if attempt == attempts - 1:
                raise RuntimeError(f"GBIF failed at offset {offset}: {exc}") from exc
            time.sleep(min(2 ** attempt, 12))
def normalize(item):
    name = item.get("canonicalName") or item.get("scientificName")
    key = item.get("key")
    if (item.get("kingdom") != "Plantae" or item.get("rank") != "SPECIES"
        or item.get("taxonomicStatus") != "ACCEPTED" or not item.get("family")
        or not name or not isinstance(key, int)):
        return None
    if not re.fullmatch(r"[A-Z][a-z-]+ [a-z-]+", name):
        return None
    return {
        "candidate_id": f"gbif_{key}", "scientific": name,
        "family": item["family"], "gbif_taxon_key": key,
        "taxonomy_status": "ACCEPTED", "intake_status": "taxonomy_only",
        "feeding_verdict": None, "nutrition_status": "unresearched",
        "feeding_evidence_status": "not_searched",
        "source": {"name": "GBIF Backbone Taxonomy", "url": f"https://www.gbif.org/species/{key}",
                   "source_type": "taxonomy", "supports_feeding_claim": False}
    }
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--limit", type=int, default=1000)
    parser.add_argument("--pages", type=int, default=5)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.offset < 0 or not 1 <= args.limit <= 1000 or args.pages < 1:
        parser.error("offset>=0, limit=1..1000 and pages>=1 required")
    existing = json.loads((ROOT / "data/plants.json").read_text(encoding="utf-8"))
    known = {p["scientific"].casefold() for p in existing if p.get("scientific")}
    found = {}
    offsets = []
    for page in range(args.pages):
        offset = args.offset + page * args.limit
        data = fetch_page(offset, args.limit)
        offsets.append(offset)
        for item in data.get("results", []):
            record = normalize(item)
            if record and record["scientific"].casefold() not in known:
                found[record["candidate_id"]] = record
        if data.get("endOfRecords"):
            break
        time.sleep(0.3)
    payload = {
        "metadata": {"dataset": "GBIF Backbone", "scope": "global vascular plants",
            "retrieved_utc": datetime.now(timezone.utc).isoformat(),
            "source_api": API, "offsets": offsets, "page_size": args.limit,
            "existing_plant_count": len(existing), "candidate_count": len(found),
            "warning": "Taxonomic discovery only. No tortoise feeding evidence or safety verdict."},
        "candidates": list(found.values())
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Saved {len(found)} taxonomic candidates to {args.output}")
if __name__ == "__main__":
    main()
