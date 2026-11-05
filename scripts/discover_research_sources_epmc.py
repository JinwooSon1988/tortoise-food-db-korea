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
import urllib.error
import urllib.request
from pathlib import Path

DOI_RE = re.compile(r"^https?://(?:dx\.)?doi\.org/(10\..+)$", re.I)

def normalize_title(value):
    return " ".join(re.findall(r"[a-z0-9]+", (value or "").casefold()))

def lookup(record, retries=2, timeout=18):
    url = record["source_url"]
    match = DOI_RE.match(url)
    base = {"source_url": url, "queue_title": record["title"],
            "candidate_taxon_count": len(record["taxon_associations"]),
            "feeding_safety_status": "unassessed",
            "plant_associations_verified": 0}
    doi = urllib.parse.unquote(match.group(1)) if match else None
    title = record["title"].strip()
    if not doi and not normalize_title(title):
        return {**base, "discovery_status": "non_doi_no_title"}
    query_text = ('DOI:"' + doi.replace('"', '') + '"') if doi else ('TITLE:"' + title.replace('"', '') + '"')
    query = urllib.parse.urlencode({"query": query_text,
                                     "format": "json", "pageSize": "10"})
    endpoint = "https://www.ebi.ac.uk/europepmc/webservices/rest/search?" + query
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(endpoint, headers={
                "User-Agent": "GeobukbapResearchDiscovery/1.0 (academic metadata only)",
                "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as response:
                data = json.load(response)
            hits = data.get("resultList", {}).get("result", [])
            exact = ([x for x in hits if (x.get("doi") or "").lower() == doi.lower()]
                     if doi else [x for x in hits if normalize_title(x.get("title")) == normalize_title(title)])
            if not exact:
                return {**base, "doi": doi,
                        "discovery_status": "not_found_exact_doi" if doi else "not_found_exact_title"}
            x = exact[0]
            return {**base, "doi": doi or x.get("doi"),
                    "match_method": "exact_doi" if doi else "normalized_exact_title",
                    "discovery_status": "metadata_matched",
                    "epmc_id": x.get("id"), "pmid": x.get("pmid"),
                    "pmcid": x.get("pmcid"), "title": x.get("title"),
                    "journal": x.get("journalTitle"), "year": x.get("pubYear"),
                    "is_open_access": x.get("isOpenAccess"),
                    "has_full_text": x.get("hasTextMinedTerms"),
                    "metadata_only": True}
        except (OSError, ValueError, TimeoutError) as exc:
            http_code = exc.code if isinstance(exc, urllib.error.HTTPError) else None
            retryable = http_code is None or http_code in (408, 429, 500, 502, 503, 504)
            if attempt == retries or not retryable:
                return {**base, "doi": doi, "discovery_status": "lookup_error",
                        "error_type": type(exc).__name__, "http_status": http_code,
                        "attempts": attempt + 1}
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
    # Probe a small batch before launching hundreds of concurrent requests.
    # A uniform permanent HTTP denial opens the circuit for this run.
    probe = [lookup(r) for r in records[:3]]
    denied = len(probe) == 3 and all(
        r.get("http_status") in (401, 403) and
        r.get("http_status") == probe[0].get("http_status")
        for r in probe
    )
    if denied:
        result = probe + [
            {"source_url": r["source_url"], "queue_title": r["title"],
             "candidate_taxon_count": len(r["taxon_associations"]),
             "feeding_safety_status": "unassessed",
             "plant_associations_verified": 0,
             "discovery_status": "lookup_error",
             "error_type": "circuit_open_after_permanent_http_denial",
             "http_status": probe[0]["http_status"], "attempts": 0}
            for r in records[3:]
        ]
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
            result = probe + list(pool.map(lookup, records[3:]))
    assert len(result) == len(records)
    assert len({r["source_url"] for r in result}) == len(records)
    statuses = {}
    for r in result:
        statuses[r["discovery_status"]] = statuses.get(r["discovery_status"], 0) + 1
        assert r["feeding_safety_status"] == "unassessed"
        assert r["plant_associations_verified"] == 0
    unmatched = [r for r in result if r["discovery_status"] != "metadata_matched"]
    matched = [r for r in result if r["discovery_status"] == "metadata_matched"]
    full_text_candidates = [r for r in matched if r.get("pmcid")]
    payload = {"schema_version": "1.1", "purpose": "source discovery only; no plant feeding validation",
               "total_sources": len(result), "status_counts": statuses,
               "matched_sources": len(matched),
               "pmc_full_text_candidates": len(full_text_candidates),
               "unmatched_sources": len(unmatched),
               "records": result}
    output_path = Path(args.out)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    (output_path.parent / "epmc_unmatched_sources.json").write_text(
        json.dumps({"count": len(unmatched), "records": unmatched}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    (output_path.parent / "epmc_full_text_candidates.json").write_text(
        json.dumps({"count": len(full_text_candidates), "records": full_text_candidates},
                   ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"sources": len(result), "statuses": statuses}))

if __name__ == "__main__":
    main()
