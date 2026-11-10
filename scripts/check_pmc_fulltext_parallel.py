#!/usr/bin/env python3
"""Parallel PMC full-text availability checks, not plant feeding verification.

Queries Europe PMC JATS XML for PMC-linked source records and records availability,
document size, and section counts. Never claims taxon or feeding evidence.
"""
import argparse
import concurrent.futures
import json
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

def check(record, retries=2, timeout=25, cache_dir=None):
    base = {"source_url": record["source_url"], "pmcid": record["pmcid"],
            "feeding_safety_status": "unassessed",
            "plant_associations_verified": 0}
    pmcid = record["pmcid"]
    if not isinstance(pmcid, str) or not pmcid.startswith("PMC") or not pmcid[3:].isdigit():
        return {**base, "status": "invalid_pmcid"}
    if cache_dir is not None:
        cached = Path(cache_dir) / (pmcid + ".xml")
        if cached.is_file():
            try:
                payload = cached.read_bytes()
                if len(payload) <= 12_000_000:
                    root = ET.fromstring(payload)
                    if root.tag.split("}")[-1] == "article":
                        return {**base, "status": "full_text_xml_available",
                                "xml_bytes": len(payload),
                                "article_sections": sum(
                                    1 for node in root.iter()
                                    if node.tag.split("}")[-1] == "sec"),
                                "cache_hit": True}
            except (OSError, ET.ParseError):
                pass  # Invalid cache is never trusted; revalidate from the provider.
    endpoint = "https://www.ebi.ac.uk/europepmc/webservices/rest/" + pmcid + "/fullTextXML"
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(endpoint, headers={
                "User-Agent": "GeobukbapFullTextAvailability/1.0",
                "Accept": "application/xml"})
            with urllib.request.urlopen(req, timeout=timeout) as response:
                payload = response.read(12_000_001)
            if len(payload) > 12_000_000:
                return {**base, "status": "size_limit_exceeded"}
            try:
                root = ET.fromstring(payload)
            except ET.ParseError:
                return {**base, "status": "invalid_xml"}
            if root.tag.split("}")[-1] != "article":
                return {**base, "status": "unexpected_xml_root"}
            if cache_dir is not None:
                cache = Path(cache_dir)
                cache.mkdir(parents=True, exist_ok=True)
                target = cache / (pmcid + ".xml")
                temporary = cache / (pmcid + ".xml.tmp")
                temporary.write_bytes(payload)
                temporary.replace(target)
            return {**base, "status": "full_text_xml_available",
                    "xml_bytes": len(payload),
                    "article_sections": sum(1 for node in root.iter()
                                            if node.tag.split("}")[-1] == "sec")}
        except urllib.error.HTTPError as exc:
            if exc.code in (404, 403):
                return {**base, "status": "full_text_unavailable", "http_status": exc.code}
            if attempt == retries:
                return {**base, "status": "request_error", "http_status": exc.code, "attempts": attempt + 1}
        except (OSError, ValueError, TimeoutError):
            if attempt == retries:
                return {**base, "status": "request_error", "attempts": attempt + 1}
        time.sleep(0.5 * 2 ** attempt)

def eligible_for_second_pass(row):
    """Avoid re-requesting persistent HTTP 500 responses in the same run."""
    return row["status"] == "request_error" and row.get("http_status") != 500


def merge_retry_results(previous, retried):
    """Preserve successful checks and replace only transient request errors."""
    old = {r["source_url"]: r for r in previous["records"]}
    retry_urls = {r["source_url"] for r in previous["records"] if eligible_for_second_pass(r)}
    assert len(old) == len(previous["records"])
    assert len({r["source_url"] for r in retried}) == len(retried)
    assert {r["source_url"] for r in retried} <= retry_urls
    for row in retried:
        old[row["source_url"]] = row
    records = [old[r["source_url"]] for r in previous["records"]]
    counts = {}
    for row in records:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    return {**previous, "status_counts": counts, "records": records,
            "retry_attempted": len(retried),
            "retry_recovered": sum(r["status"] == "full_text_xml_available" for r in retried),
            "retry_skipped_http_500": sum(r["status"] == "request_error" and r.get("http_status") == 500
                                           for r in previous["records"])}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--candidates", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--workers", type=int, default=8)
    p.add_argument("--cache-dir", help="Save validated XML locally for extraction without a second download")
    p.add_argument("--retry-errors-from", help="Previous availability JSON; recheck only request_error records")
    args = p.parse_args()
    if not 1 <= args.workers <= 16:
        p.error("workers must be between 1 and 16")
    candidates = json.loads(Path(args.candidates).read_text(encoding="utf-8"))["records"]
    previous = None
    if args.retry_errors_from:
        previous = json.loads(Path(args.retry_errors_from).read_text(encoding="utf-8"))
        errors = {r["source_url"] for r in previous["records"] if eligible_for_second_pass(r)}
        assert {r["source_url"] for r in previous["records"]} == {r["source_url"] for r in candidates}
        candidates = [r for r in candidates if r["source_url"] in errors]
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(lambda record: check(record, cache_dir=args.cache_dir), candidates))
    assert len(results) == len(candidates)
    assert len({x["source_url"] for x in results}) == len(results)
    assert all(x["feeding_safety_status"] == "unassessed" and
               x["plant_associations_verified"] == 0 for x in results)
    counts = {}
    for x in results:
        counts[x["status"]] = counts.get(x["status"], 0) + 1
    payload = {"schema_version": "1.0",
               "scope": "full-text availability only, NOT feeding evidence review",
               "total_candidates": len(results), "status_counts": counts,
               "records": results}
    if previous is not None:
        payload = merge_retry_results(previous, results)
    Path(args.out).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"candidates": len(results), "statuses": counts}))

if __name__ == "__main__":
    main()
