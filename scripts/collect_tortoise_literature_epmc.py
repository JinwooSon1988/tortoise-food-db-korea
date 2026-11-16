#!/usr/bin/env python3
"""Parallel Europe PMC literature discovery; publications are NOT plant feeding verdicts."""
import argparse
import concurrent.futures
import json
import os
import tempfile
from datetime import date
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
QUERIES = (
    '("Testudo graeca" OR "Testudo hermanni") AND (diet OR feeding OR forage)',
    '("Centrochelys sulcata" OR "Geochelone sulcata") AND (diet OR feeding OR plants)',
    '("Gopherus agassizii" OR "Gopherus polyphemus") AND (diet OR forage OR vegetation)',
    '("Aldabrachelys gigantea" OR "Chelonoidis") AND (diet OR feeding OR vegetation)',
    '("Testudo marginata" OR "Agrionemys horsfieldii") AND (diet OR forage OR vegetation)',
    '(tortoise OR tortoises) AND ("food plants" OR "diet composition" OR "feeding ecology")',
)


def fetch(query, page_size, opener=urlopen):
    url = API + "?" + urlencode({"query": query, "format": "json", "pageSize": page_size,
                                  "resultType": "core"})
    req = Request(url, headers={"Accept": "application/json",
                                 "User-Agent": "GeobukbapResearch/1.0"})
    with opener(req, timeout=25) as response:
        payload = json.load(response)
    rows = payload.get("resultList", {}).get("result")
    if not isinstance(rows, list):
        raise ValueError("invalid Europe PMC search response")
    return rows


def collect(output, report, workers=6, page_size=100, fetcher=fetch):
    if not 1 <= workers <= 12 or not 1 <= page_size <= 1000:
        raise ValueError("invalid concurrency or page size")
    if output.resolve() == report.resolve() or output.exists() or report.exists():
        raise ValueError("distinct new output and report paths required")
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
            item = {"source": "Europe PMC", "source_database": source, "source_record_id": identifier,
                    "source_url": "https://europepmc.org/article/" + source + "/" + identifier,
                    "doi": doi if isinstance(doi, str) else None,
                    "title": title, "journal": article.get("journalTitle"),
                    "publication_year": article.get("pubYear"),
                    "observed_at": date.today().isoformat(),
                    "matching_queries": [],
                    "review_status": "unmatched_literature_lead",
                    "plant_scientific_name": None, "plant_part": None,
                    "tortoise_scientific_name": None, "feeding_verdict": None}
            if key in unique:
                prior = unique[key]
                if prior["title"] != title or prior["doi"] != item["doi"]:
                    raise ValueError(f"conflicting publication metadata: {key}")
            else:
                unique[key] = item
            unique[key]["matching_queries"].append(query)
    if not unique:
        raise ValueError("zero publications: refusing empty output")
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
                json.dump({"queries": len(QUERIES), "raw_hits": occurrences, "unique_publications": len(unique),
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
    return {"queries": len(QUERIES), "raw_hits": occurrences, "unique_publications": len(unique)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--page-size", type=int, default=100)
    args = parser.parse_args()
    print(json.dumps(collect(args.output, args.report, args.workers, args.page_size), sort_keys=True))
