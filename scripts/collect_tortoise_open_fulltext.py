#!/usr/bin/env python3
"""Parallel open-access full-text retrieval for human review, never feeding verdicts."""
import argparse
import concurrent.futures
import json
import re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE = "https://www.ebi.ac.uk/europepmc/webservices/rest/"
MAX_CHARS = 250000


def retrieve(pmcid, opener=urlopen):
    if not re.fullmatch(r"PMC[0-9]+", pmcid):
        raise ValueError("invalid PMC identifier")
    req = Request(BASE + pmcid + "/fullTextXML",
                  headers={"User-Agent": "GeobukbapResearch/1.0"})
    try:
        with opener(req, timeout=18) as response:
            raw = response.read(3000000)
    except (HTTPError, URLError, TimeoutError):
        return None
    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        return None
    body = root.find(".//body")
    if body is None:
        return None
    text = " ".join(" ".join(body.itertext()).split())
    return text[:MAX_CHARS] if text else None


def enrich(corpus, output, report, workers=12, fetcher=retrieve):
    if not 1 <= workers <= 12:
        raise ValueError("workers must be between 1 and 12")
    if len({p.resolve() for p in (corpus, output, report)}) != 3 or output.exists() or report.exists():
        raise ValueError("paths must be distinct and outputs new")
    items = []
    seen = set()
    with corpus.open(encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            row = json.loads(line)
            key = (row.get("source_database"), str(row.get("source_record_id") or ""))
            if not all(key) or key in seen:
                raise ValueError("duplicate/missing publication identity")
            seen.add(key)
            if key[0] == "PMC" and re.fullmatch(r"PMC[0-9]+", key[1]):
                items.append(row)
    if not seen:
        raise ValueError("empty corpus")
    results = []
    counts = Counter({"total_publications": len(seen), "pmc_candidates": len(items)})
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(fetcher, row["source_record_id"]) for row in items]
        for row, future in zip(items, futures):
            try:
                text = future.result()
            except Exception:
                counts["retrieval_errors"] += 1
                continue
            if not text:
                counts["unavailable_fulltext"] += 1
                continue
            results.append({"source_database": row["source_database"],
                            "source_record_id": row["source_record_id"],
                            "source_url": row["source_url"],
                            "source_title": row.get("title"),
                            "fulltext_excerpt": text,
                            "truncated": len(text) == MAX_CHARS,
                            "review_status": "unverified_fulltext_for_manual_review",
                            "feeding_verdict": None})
            counts["fulltexts_retrieved"] += 1
    output.parent.mkdir(parents=True, exist_ok=True)
    report.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as stream:
        for row in results:
            stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    with report.open("x", encoding="utf-8") as stream:
        json.dump({"counts": dict(counts), "status": "review_only_no_feeding_verdicts"},
                  stream, indent=2)
        stream.write("\n")
    return dict(counts)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("corpus", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--workers", type=int, default=12)
    args = parser.parse_args()
    print(json.dumps(enrich(args.corpus, args.output, args.report, args.workers), sort_keys=True))
