#!/usr/bin/env python3
"""Bounded parallel discovery of tortoise diet literature; no feeding safety claims."""
import argparse
import concurrent.futures
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

QUERIES = (
    'TITLE_ABS:(tortoise AND (diet OR feeding OR forage OR foraging))',
    'TITLE_ABS:(Testudo AND (diet OR feeding OR food OR grazing))',
    'TITLE_ABS:(Gopherus AND (diet OR feeding OR forage))',
    'TITLE_ABS:(Chelonoidis AND (diet OR feeding OR food))',
    'TITLE_ABS:(Stigmochelys AND (diet OR feeding OR grazing))',
    'TITLE_ABS:(Centrochelys AND (diet OR feeding OR grazing))',
    'TITLE_ABS:(Kinixys AND (diet OR feeding OR food))',
    'TITLE_ABS:(Aldabrachelys AND (diet OR feeding OR food))',
    'TITLE_ABS:(Astrochelys AND (diet OR feeding OR food))',
    'TITLE_ABS:(Manouria AND (diet OR feeding OR food))',
    'TITLE_ABS:(Indotestudo AND (diet OR feeding OR food))',
    'TITLE_ABS:(Psammobates AND (diet OR feeding OR food))',
)

def search(query, retries=2, timeout=20):
    url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search?" + urllib.parse.urlencode(
        {"query": query, "format": "json", "pageSize": "100", "sort": "RELEVANCE"})
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "GeobukbapDietLiteratureDiscovery/1.0",
                "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as response:
                data = json.load(response)
            hits = data.get("resultList", {}).get("result", [])
            return {"query": query, "status": "ok", "reported_hits": data.get("hitCount", 0),
                    "records": hits}
        except (OSError, ValueError, TimeoutError) as exc:
            code = exc.code if isinstance(exc, urllib.error.HTTPError) else None
            if attempt == retries or code not in (None, 408, 429, 500, 502, 503, 504):
                return {"query": query, "status": "error", "http_status": code,
                        "error_type": type(exc).__name__, "records": []}
            time.sleep(0.5 * 2 ** attempt)

def combine(results):
    records = {}
    for result in results:
        if result["status"] != "ok":
            continue
        for hit in result["records"]:
            doi = (hit.get("doi") or "").strip().lower()
            pmid = str(hit.get("pmid") or "").strip()
            pmcid = (hit.get("pmcid") or "").strip()
            key = ("doi:" + doi if doi else "pmid:" + pmid if pmid else
                   "pmcid:" + pmcid if pmcid else
                   "epmc:" + str(hit.get("source", "")) + ":" + str(hit.get("id", "")))
            if key.endswith(":"):
                continue
            if key not in records:
                records[key] = {"source_key": key, "title": hit.get("title"),
                                "doi": hit.get("doi"), "pmid": hit.get("pmid"),
                                "pmcid": hit.get("pmcid"), "year": hit.get("pubYear"),
                                "journal": hit.get("journalTitle"),
                                "matched_queries": [],
                                "review_status": "not_reviewed",
                                "feeding_observation_status": "not_verified",
                                "feeding_safety_status": "unassessed",
                                "verified_plant_links": []}
            if result["query"] not in records[key]["matched_queries"]:
                records[key]["matched_queries"].append(result["query"])
    output = sorted(records.values(), key=lambda r: (-len(r["matched_queries"]), r["source_key"]))
    return {"schema_version": "1.0", "scope": "unverified literature leads only",
            "queries": len(results), "queries_succeeded": sum(r["status"] == "ok" for r in results),
            "queries_failed": sum(r["status"] != "ok" for r in results),
            "unique_sources": len(output),
            "query_diagnostics": [{k: v for k, v in r.items() if k != "records"} for r in results],
            "records": output}

def uniform_provider_outage(probe):
    return len(probe) == 3 and all(
        r["status"] == "error" and r.get("http_status") in (429, 502, 503, 504)
        and r.get("http_status") == probe[0].get("http_status")
        for r in probe)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", required=True)
    p.add_argument("--workers", type=int, default=6)
    args = p.parse_args()
    if not 1 <= args.workers <= 12:
        p.error("workers must be between 1 and 12")
    # Probe before fan-out: a uniform provider outage must not trigger 12 full retries.
    probe = [search(q) for q in QUERIES[:3]]
    uniform_outage = uniform_provider_outage(probe)
    if uniform_outage:
        results = probe + [
            {"query": q, "status": "error",
             "http_status": probe[0]["http_status"],
             "error_type": "circuit_open_after_uniform_http_failure",
             "records": []} for q in QUERIES[3:]]
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
            results = probe + list(pool.map(search, QUERIES[3:]))
    result = combine(results)
    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("queries", "queries_succeeded", "queries_failed", "unique_sources")}))
    if result["queries_failed"]:
        raise SystemExit("Incomplete tortoise diet literature discovery; partial unverified output preserved")

if __name__ == "__main__":
    main()
