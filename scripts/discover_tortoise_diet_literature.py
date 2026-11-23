#!/usr/bin/env python3
"""Bounded literature-first discovery. Unreviewed works never imply safe feeding."""
import argparse
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

TAXA = ("Testudo graeca", "Testudo hermanni", "Testudo marginata",
        "Centrochelys sulcata", "Stigmochelys pardalis",
        "Gopherus agassizii", "Gopherus polyphemus", "Chelonoidis carbonarius")
TOPICS = ("diet", "food plants", "feeding ecology", "foraging")
QUERIES = tuple((taxon, topic) for taxon in TAXA for topic in TOPICS)


def build_url(taxon, topic):
    return "https://api.openalex.org/works?" + urllib.parse.urlencode({
        "search": f'"{taxon}" "{topic}"',
        "per-page": "25",
        "select": "id,doi,title,publication_year,primary_location",
    })


def collect(fetch, sleep, start=0, limit=8, interval=3.0):
    """Fixed query windows; deduplicate by stable OpenAlex ID; fail on HTTP errors."""
    if start < 0 or limit < 1 or interval < 1:
        raise ValueError("invalid bounds or API interval")
    works = {}
    query_report = []
    for i, (taxon, topic) in enumerate(QUERIES[start:start + limit], start):
        if query_report:
            sleep(interval)
        data = fetch(build_url(taxon, topic))
        if not isinstance(data.get("results"), list):
            raise ValueError("invalid OpenAlex response")
        hits = 0
        for work in data["results"]:
            identifier = work.get("id")
            if not isinstance(identifier, str) or not identifier.startswith("https://openalex.org/W"):
                continue
            hits += 1
            if identifier not in works:
                works[identifier] = {
                    "openalex_id": identifier,
                    "doi": work.get("doi"),
                    "title": work.get("title"),
                    "year": work.get("publication_year"),
                    "source_url": (work.get("primary_location") or {}).get("landing_page_url"),
                    "status": "literature_lead_unreviewed",
                    "query_matches": [],
                    "feeding_confirmed": False,
                }
            works[identifier]["query_matches"].append({"taxon": taxon, "topic": topic})
        query_report.append({"index": i, "taxon": taxon, "topic": topic, "hits": hits})
    return {
        "scope": "literature_first_unreviewed_not_feeding_evidence",
        "query_start": start, "query_limit": limit,
        "queries_completed": len(query_report),
        "unique_works": len(works),
        "feeding_verdicts_confirmed": 0,
        "queries": query_report,
        "works": sorted(works.values(), key=lambda w: w["openalex_id"]),
    }


def fetch_json(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": "GeobukbapResearch/0.1 (research-only; repository issues)",
        "Accept": "application/json",
    })
    with urllib.request.urlopen(req, timeout=25) as response:
        return json.load(response)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--interval", type=float, default=3.0)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.start + args.limit > len(QUERIES):
        parser.error("query window exceeds available research queries")
    report = collect(fetch_json, time.sleep, args.start, args.limit, args.interval)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("queries_completed", "unique_works", "feeding_verdicts_confirmed")}))


if __name__ == "__main__":
    main()
