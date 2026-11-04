#!/usr/bin/env python3
"""Parallel Europe PMC discovery for unique research DOI sources.

Output is an auditable *discovery* artifact, never proof of consumption/safety.
Uses bounded parallelism, retry, and an explicit result for every source.
"""
import argparse
import concurrent.futures
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

DOI_RE = re.compile(r"^https?://(?:dx\\.)?doi\\.org/(10\\..+)$", re.I)

def lookup(record, retries=2, timeout=18):
    url = record["source_url"]
    match = DOI_RE.match(url)
    base = {"source_url": url, "queue_title": record["title"],
            "candidate_taxon_count": len(record["taxon_associations"]),
            "feeding_safety_status": "unassessed",
            "plant_associations_verified": 0}
    if not match:
        return {**base, "discovery_status": "non_doi_url"}
    doi = urllib.parse.unquote(match.group(1))
    query = urllib.parse.urlencode({"query": 'DOI:"' + doi.replace('"', '') + '"',
                                     "format": "json", "pageSize": "5"})
    endpoint = "https://www.ebi.ac.uk/europepmc/webservices/rest/search?" + query
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(endpoint, headers={
                "User-Agent": "GeobukbapResearchDiscovery/1.0 (academic metadata only)",
                "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as response:
                data = json.load(response)
            hits = data.get("resultList", {}).get("result", [])
            exact = [x for x in hits if x.get("doi", "").lower() == doi.lower()]
            if not exact:
                return {**base, "doi": doi, "discovery_status": "not_found_exact_doi"}
            x = exact[0]
            return {**base, "doi": doi, "discovery_status": "metadata_matched",
                    "epmc_id": x.get("id"), "pmid": x.get("pmid"),
                    "pmcid": x.get("pmcid"), "title": x.get("title"),
                    "journal": x.get("journalTitle"), "year": x.get("pubYear"),
                    "is_open_access": x.get("isOpenAccess"),
                    "has_full_text": x.get("hasTextMinedTerms"),
                    "metadata_only": True}
        except (OSError, ValueError, TimeoutError) as exc:
            if attempt == retries:
                return {**base, "doi": doi, "discovery_status": "lookup_error",
                        "error_type": type(exc).__name__}
            time.sleep(0.5 * (2 ** attempt))

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--queue", default="data/research_unique_source_review_queue.json")
    p.add_argument("--out", required=True)
    p.add_argument("--workers", type=int, default=12)
    p.add_argument("--limit", type=int, default=0, help="Optional diagnostic sample size")
    args = p.parse_args()
    if not 1 <= args.workers <= 24:
        p.error("--workers must be between 1 and 24")
    records = json.loads(Path(args.queue).read_text(encoding="utf-8"))["records"]
    if args.limit:
        records = records[:args.limit]
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        result = list(pool.map(lookup, records))
    assert len(result) == len(records)
    assert len({r["source_url"] for r in result}) == len(records)
    statuses = {}
    for r in result:
        statuses[r["discovery_status"]] = statuses.get(r["discovery_status"], 0) + 1
        assert r["feeding_safety_status"] == "unassessed"
        assert r["plant_associations_verified"] == 0
    payload = {"schema_version": "1.0", "purpose": "source discovery only; no plant feeding validation",
               "total_sources": len(result), "status_counts": statuses, "records": result}
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"sources": len(result), "statuses": statuses}))

if __name__ == "__main__":
    main()
