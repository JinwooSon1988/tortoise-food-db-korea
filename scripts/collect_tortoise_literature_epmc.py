#!/usr/bin/env python3
"""Parallel Europe PMC literature discovery; publications are NOT plant feeding verdicts."""
import argparse
import concurrent.futures
import json
import os
import tempfile
import time
from datetime import date
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

API = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
QUERIES = (
    '("Testudo graeca" OR "Testudo hermanni") AND (diet OR feeding OR forage)',
    '("Centrochelys sulcata" OR "Geochelone sulcata") AND (diet OR feeding OR plants)',
    '("Gopherus agassizii" OR "Gopherus polyphemus") AND (diet OR forage OR vegetation)',
    '("Aldabrachelys gigantea" OR "Chelonoidis") AND (diet OR feeding OR vegetation)',
    '("Testudo marginata" OR "Agrionemys horsfieldii") AND (diet OR forage OR vegetation)',
    '(tortoise OR tortoises) AND ("food plants" OR "diet composition" OR "feeding ecology")',
    '("Testudo ibera" OR "Testudo kleinmanni") AND (diet OR feeding OR vegetation)',
    '("Stigmochelys pardalis" OR "Geochelone pardalis") AND (diet OR forage OR plants)',
    '("Astrochelys radiata" OR "Pyxis arachnoides") AND (diet OR forage OR feeding)',
    '("Kinixys" OR "Malacochersus") AND (diet OR forage OR feeding)',
    '("Manouria emys" OR "Indotestudo elongata") AND (diet OR plants OR feeding)',
    '("Homopus" OR "Chersobius" OR "Psammobates") AND (diet OR plants OR feeding)',
)


def request_json_with_retry(req, opener=urlopen, sleeper=time.sleep):
    """Retry temporary upstream failures; fail closed with the original exception."""
    for attempt in range(6):
        try:
            with opener(req, timeout=25) as response:
                return json.load(response)
        except HTTPError as error:
            if error.code not in (429, 500, 502, 503, 504):
                raise
            if attempt == 5:
                raise
        except (URLError, TimeoutError):
            if attempt == 5:
                raise
        sleeper(min(8.0, 0.5 * (2 ** attempt)))


def fetch(query, page_size, opener=urlopen):
    url = API + "?" + urlencode({"query": query, "format": "json", "pageSize": page_size,
                                  "resultType": "core"})
    req = Request(url, headers={"Accept": "application/json",
                                 "User-Agent": "GeobukbapResearch/1.0"})
    payload = request_json_with_retry(req, opener=opener)
    rows = payload.get("resultList", {}).get("result")
    if not isinstance(rows, list):
        raise ValueError("invalid Europe PMC search response")
    return rows



def fetch_pages(query, page_size, max_pages=3, opener=urlopen):
    """Fetch bounded Europe PMC cursor pages, preserving all returned records."""
    if not 1 <= max_pages <= 10:
        raise ValueError("max_pages must be 1..10")
    rows = []
    cursor = "*"
    seen_cursors = set()
    for _ in range(max_pages):
        if cursor in seen_cursors:
            raise ValueError("repeated Europe PMC cursor")
        seen_cursors.add(cursor)
        url = API + "?" + urlencode({"query": query, "format": "json",
                                      "pageSize": page_size, "resultType": "core",
                                      "cursorMark": cursor})
        req = Request(url, headers={"Accept": "application/json",
                                     "User-Agent": "GeobukbapResearch/1.0"})
        payload = request_json_with_retry(req, opener=opener)
        batch = payload.get("resultList", {}).get("result")
        if not isinstance(batch, list):
            raise ValueError("invalid Europe PMC search response")
        rows.extend(batch)
        next_cursor = payload.get("nextCursorMark")
        if len(batch) < page_size or not next_cursor or next_cursor == cursor:
            break
        if not isinstance(next_cursor, str):
            raise ValueError("invalid Europe PMC cursor")
        cursor = next_cursor
    return rows


def collect(output, report, workers=12, page_size=100, fetcher=None, max_pages=3):
    if not 1 <= workers <= 12 or not 1 <= page_size <= 1000 or not 1 <= max_pages <= 10:
        raise ValueError("invalid concurrency or page size")
    if output.resolve() == report.resolve() or output.exists() or report.exists():
        raise ValueError("distinct new output and report paths required")
    if fetcher is None:
        fetcher = lambda query, size: fetch_pages(query, size, max_pages=max_pages)
    # Fail closed: all searches must succeed before publishing anything.
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(fetcher, query, page_size) for query in QUERIES]
        results = [future.result() for future in futures]
    unique = {}
    occurrences = 0
    for query, articles in zip(QUERIES, results):
        for article in articles:
            occurrences += 1
            if not isinstance(article, dict):
                raise ValueError("invalid article")
            identifier = str(article.get("id") or "").strip()
            source = str(article.get("source") or "").strip()
            title = str(article.get("title") or "").strip()
            if not identifier or not source or not title:
                continue
            key = (source, identifier)
            doi = article.get("doi")
            pmcid = article.get("pmcid")
            pmcid = pmcid.strip() if isinstance(pmcid, str) else None
            if pmcid and not (pmcid.startswith("PMC") and pmcid[3:].isdigit()):
                pmcid = None
            abstract = article.get("abstractText")
            abstract = abstract.strip() if isinstance(abstract, str) else None
            item = {"source": "Europe PMC", "source_database": source, "source_record_id": identifier,
                    "source_url": "https://europepmc.org/article/" + source + "/" + identifier,
                    "doi": doi if isinstance(doi, str) else None, "pmcid": pmcid,
                    "title": title, "abstract_text": abstract, "journal": article.get("journalTitle"),
                    "publication_year": article.get("pubYear"),
                    "observed_at": date.today().isoformat(),
                    "matching_queries": [],
                    "review_status": "unmatched_literature_lead",
                    "plant_scientific_name": None, "plant_part": None,
                    "tortoise_scientific_name": None, "feeding_verdict": None}
            if key in unique:
                prior = unique[key]
                if (prior["title"] != title or prior["doi"] != item["doi"]
                        or (prior["pmcid"] and pmcid and prior["pmcid"] != pmcid)
                        or (prior["abstract_text"] and abstract and prior["abstract_text"] != abstract)):
                    raise ValueError(f"conflicting publication metadata: {key}")
                if not prior["pmcid"] and pmcid:
                    prior["pmcid"] = pmcid
                if not prior["abstract_text"] and abstract:
                    prior["abstract_text"] = abstract
            else:
                unique[key] = item
            unique[key]["matching_queries"].append(query)
    if not unique:
        raise ValueError("zero publications: refusing empty output")
    abstract_count = sum(bool(item["abstract_text"]) for item in unique.values())
    output.parent.mkdir(parents=True, exist_ok=True)
    report.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".epmc-", dir=output.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            for key in sorted(unique):
                stream.write(json.dumps(unique[key], ensure_ascii=False, sort_keys=True) + "\n")
        fd2, tmp2 = tempfile.mkstemp(prefix=".epmc-report-", dir=report.parent)
        try:
            with os.fdopen(fd2, "w", encoding="utf-8") as stream:
                json.dump({"queries": len(QUERIES), "raw_hits": occurrences, "unique_publications": len(unique), "with_abstract": abstract_count,
                           "status": "unmatched_literature_leads_only",
                           "note": "No plant, tortoise species or feeding verdict inferred from search results."},
                          stream, indent=2)
                stream.write("\n")
            os.replace(tmp, output)
            os.replace(tmp2, report)
        finally:
            if os.path.exists(tmp2):
                os.unlink(tmp2)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    return {"queries": len(QUERIES), "raw_hits": occurrences, "unique_publications": len(unique),
            "with_abstract": abstract_count}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=12)
    parser.add_argument("--max-pages", type=int, default=3)
    parser.add_argument("--page-size", type=int, default=100)
    args = parser.parse_args()
    print(json.dumps(collect(args.output, args.report, args.workers, args.page_size, max_pages=args.max_pages), sort_keys=True))
