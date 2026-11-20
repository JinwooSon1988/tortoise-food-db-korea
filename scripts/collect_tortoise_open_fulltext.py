#!/usr/bin/env python3
"""Parallel open-access full-text retrieval for human review, never feeding verdicts."""
import argparse
import concurrent.futures
import json
import tempfile
import re
import threading
import time
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE = "https://www.ebi.ac.uk/europepmc/webservices/rest/"
MAX_CHARS = 250000
MAX_XML_BYTES = 12_000_000
# Bound concurrent requests independently of the number of parsing workers.
PMC_REQUEST_SLOTS = threading.BoundedSemaphore(8)
RETRY_ATTEMPTS = 3



BLOCK_TAGS = {"p", "title", "sec", "tr", "table-wrap", "list-item", "caption"}


def extract_structured_body(body):
    """Retain JATS paragraph/table-row boundaries; never join separate cells into a taxon."""
    chunks = []

    def walk(node):
        tag = node.tag.rsplit("}", 1)[-1] if isinstance(node.tag, str) else ""
        if tag in BLOCK_TAGS:
            chunks.append("\n")
        if node.text:
            chunks.append(node.text)
        for child in node:
            walk(child)
            if child.tail:
                chunks.append(child.tail)
        if tag in BLOCK_TAGS:
            chunks.append("\n")
        elif tag in {"td", "th"}:
            chunks.append(" | ")

    walk(body)
    lines = [" ".join(line.split()) for line in "".join(chunks).splitlines()]
    return "\n".join(line for line in lines if line)


def retrieve(pmcid, opener=urlopen, sleeper=time.sleep):
    if not re.fullmatch(r"PMC[0-9]+", pmcid):
        raise ValueError("invalid PMC identifier")
    req = Request(BASE + pmcid + "/fullTextXML",
                  headers={"User-Agent": "GeobukbapResearch/1.0"})
    raw = None
    for attempt in range(RETRY_ATTEMPTS):
        try:
            with PMC_REQUEST_SLOTS:
                with opener(req, timeout=18) as response:
                    raw = response.read(MAX_XML_BYTES + 1)
            break
        except HTTPError as error:
            if error.code not in (429, 500, 502, 503, 504):
                return None
        except (URLError, TimeoutError):
            pass
        if attempt < RETRY_ATTEMPTS - 1:
            sleeper(min(4.0, 0.5 * (2 ** attempt)))
    if raw is None or len(raw) > MAX_XML_BYTES:
        # Do not parse a silently truncated XML document as if it were complete.
        return None
    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        return None
    body = root.find(".//{*}body")
    if body is None:
        return None
    text = extract_structured_body(body)
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
            pmcid = row.get("pmcid") or (key[1] if key[0] == "PMC" else None)
            if isinstance(pmcid, str) and re.fullmatch(r"PMC[0-9]+", pmcid):
                items.append((row, pmcid))
    if not seen:
        raise ValueError("empty corpus")
    counts = Counter({"total_publications": len(seen), "pmc_candidates": len(items)})
    unique_pmcids = sorted({pmcid for _, pmcid in items})
    counts["unique_pmc_requests"] = len(unique_pmcids)
    counts["duplicate_pmc_requests_avoided"] = len(items) - len(unique_pmcids)
    # Spool full texts incrementally; avoid retaining thousands of 250KB bodies in RAM.
    # The pool remains bounded at 12 workers and HTTP requests at eight slots.
    with tempfile.TemporaryDirectory(prefix=".pmc-fulltexts-") as scratch:
        spool_path = Path(scratch) / "fulltexts.jsonl"
        with spool_path.open("w", encoding="utf-8") as spool:
            with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
                futures = {pmcid: pool.submit(fetcher, pmcid) for pmcid in unique_pmcids}
                for row, pmcid in items:
                    future = futures[pmcid]
                    try:
                        text = future.result()
                    except Exception:
                        counts["retrieval_errors"] += 1
                        continue
                    if not text:
                        counts["unavailable_fulltext"] += 1
                        continue
                    spool.write(json.dumps({
                        "source_database": row["source_database"],
                        "source_record_id": row["source_record_id"],
                        "pmcid": pmcid,
                        "source_url": row["source_url"],
                        "source_title": row.get("title"),
                        "fulltext_excerpt": text,
                        "truncated": len(text) == MAX_CHARS,
                        "review_status": "unverified_fulltext_for_manual_review",
                        "feeding_verdict": None
                    }, ensure_ascii=False, sort_keys=True) + "\n")
                    counts["fulltexts_retrieved"] += 1
        output.parent.mkdir(parents=True, exist_ok=True)
        report.parent.mkdir(parents=True, exist_ok=True)
        with output.open("x", encoding="utf-8") as destination, spool_path.open(encoding="utf-8") as source:
            for chunk in iter(lambda: source.read(1024 * 1024), ""):
                destination.write(chunk)
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
