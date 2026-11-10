#!/usr/bin/env python3
"""Bounded parallel discovery of tortoise diet literature; no feeding safety claims."""
import argparse
import concurrent.futures
import json
import html
import re
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

TORTOISE_TITLE = re.compile(
    r"\b(?:tortoises?|Testudo|Gopherus|Chelonoidis|Geochelone|Stigmochelys|"
    r"Centrochelys|Kinixys|Aldabrachelys|Astrochelys|Indotestudo|Manouria|"
    r"Psammobates|Pyxis|Homopus)\b", re.I)
DIET_TITLE = re.compile(
    r"\b(?:diet|diets|food|feeding|forag(?:e|ing)|grazing|browse|"
    r"consum(?:e|ption)|herbivor(?:e|y|ous)|plant selection)\b", re.I)

def title_signal(title):
    title = html.unescape(re.sub(r"<[^>]+>", " ", title or ""))
    tortoise = bool(TORTOISE_TITLE.search(title)) and not bool(
        re.search(r"\btortoise beetles?\b", title, re.I))
    diet = bool(DIET_TITLE.search(title))
    return "tortoise_diet_title" if tortoise and diet else (
        "tortoise_title" if tortoise else "other_title")

def crossref_fallback(queries, timeout=20, workers=2, retries=3):
    """Rate-limited independent metadata fallback; titles are review leads only."""
    def fetch(query):
        # Keep search terms concise; Crossref bibliographic search is not Boolean.
        terms = re.findall(
            r"tortoise|Testudo|Gopherus|Chelonoidis|Stigmochelys|Centrochelys|"
            r"Kinixys|Aldabrachelys|Astrochelys|Manouria|Indotestudo|Psammobates",
            query, re.I)
        terms = " ".join(terms[:1]) + " diet feeding foraging"
        url = "https://api.crossref.org/works?" + urllib.parse.urlencode({
            "query.bibliographic": terms, "rows": "100",
            "select": "DOI,title,published,container-title"})
        for attempt in range(retries + 1):
            try:
                req = urllib.request.Request(url, headers={
                    "User-Agent": "GeobukbapResearchDiscovery/1.0 (academic metadata; contact: github.com/JinwooSon1988/tortoise-food-db-korea)",
                    "Accept": "application/json"})
                with urllib.request.urlopen(req, timeout=timeout) as response:
                    items = json.load(response).get("message", {}).get("items", [])
                hits = []
                for item in items:
                    title = (item.get("title") or [""])[0]
                    if title_signal(title) != "tortoise_diet_title":
                        continue
                    parts = (item.get("published") or {}).get("date-parts") or []
                    year = parts[0][0] if parts and parts[0] else None
                    hits.append({"doi": item.get("DOI"), "title": title,
                                 "pubYear": year,
                                 "journalTitle": (item.get("container-title") or [""])[0],
                                 "source": "CROSSREF", "id": item.get("DOI")})
                return {"query": query, "status": "ok", "provider": "crossref",
                        "reported_hits": len(items), "records": hits,
                        "attempts": attempt + 1}
            except (OSError, ValueError, TimeoutError) as exc:
                code = exc.code if isinstance(exc, urllib.error.HTTPError) else None
                retryable = code in (429, 500, 502, 503, 504) or code is None
                if attempt == retries or not retryable:
                    return {"query": query, "status": "error", "provider": "crossref",
                            "http_status": code, "error_type": type(exc).__name__,
                            "attempts": attempt + 1, "records": []}
                retry_after = exc.headers.get("Retry-After") if isinstance(exc, urllib.error.HTTPError) else None
                try:
                    delay = min(30.0, max(0.5, float(retry_after))) if retry_after else 2 ** (attempt + 1)
                except (TypeError, ValueError):
                    delay = 2 ** (attempt + 1)
                time.sleep(delay)
    # Crossref returned HTTP 429 at six concurrent workers; cap at two.
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(workers, 2)) as pool:
        return list(pool.map(fetch, queries))

def merge_provider_results(primary, fallback):
    """Preserve successful primary hits and select successful fallback per query."""
    if len(primary) != len(fallback):
        raise ValueError("Provider query counts differ")
    merged = []
    for first, second in zip(primary, fallback):
        if first["query"] != second["query"]:
            raise ValueError("Provider query order differs")
        selected = dict(first if first["status"] == "ok" else (
            second if second["status"] == "ok" else first))
        selected["provider_attempts"] = [
            {k: v for k, v in r.items() if k != "records"}
            for r in (first, second)]
        merged.append(selected)
    return merged

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
                                "metadata_provider": result.get("provider", "europe_pmc"),
                                "matched_queries": [],
                                "title_review_signal": title_signal(hit.get("title")),
                                "review_status": "not_reviewed",
                                "feeding_observation_status": "not_verified",
                                "feeding_safety_status": "unassessed",
                                "verified_plant_links": []}
            if result["query"] not in records[key]["matched_queries"]:
                records[key]["matched_queries"].append(result["query"])
    priority = {"tortoise_diet_title": 0, "tortoise_title": 1, "other_title": 2}
    output = sorted(records.values(), key=lambda r: (
        priority[r["title_review_signal"]], -len(r["matched_queries"]), r["source_key"]))
    return {"schema_version": "1.0", "scope": "unverified literature leads only",
            "queries": len(results), "queries_succeeded": sum(r["status"] == "ok" for r in results),
            "queries_failed": sum(r["status"] != "ok" for r in results),
            "providers": sorted(set(r.get("provider", "europe_pmc") for r in results)),
            "unique_sources": len(output),
            "title_signal_counts": {
                key: sum(r["title_review_signal"] == key for r in output)
                for key in ("tortoise_diet_title", "tortoise_title", "other_title")},
            "query_diagnostics": [{k: v for k, v in r.items() if k != "records"} for r in results],
            "records": output}

def uniform_provider_outage(probe):
    return len(probe) == 3 and all(
        r["status"] == "error" and r.get("http_status") in (429, 502, 503, 504)
        and r.get("http_status") == probe[0].get("http_status")
        for r in probe)

def fallback_failed_queries(primary, workers=6):
    """Try Crossref only for failed queries and retain primary successes."""
    failed_queries = [r["query"] for r in primary if r["status"] != "ok"]
    if not failed_queries:
        return primary
    fallback = crossref_fallback(failed_queries, workers=workers)
    fallback_by_query = {r["query"]: r for r in fallback}
    return [
        merge_provider_results([r], [fallback_by_query[r["query"]]])[0]
        if r["query"] in fallback_by_query else r
        for r in primary]

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
    results = fallback_failed_queries(results, workers=args.workers)
    result = combine(results)
    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("queries", "queries_succeeded", "queries_failed", "unique_sources")}))
    if result["queries_failed"]:
        raise SystemExit("Incomplete tortoise diet literature discovery; partial unverified output preserved")

if __name__ == "__main__":
    main()
