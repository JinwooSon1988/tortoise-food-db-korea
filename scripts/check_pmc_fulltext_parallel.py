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

def check(record, retries=2, timeout=25):
    base = {"source_url": record["source_url"], "pmcid": record["pmcid"],
            "feeding_safety_status": "unassessed",
            "plant_associations_verified": 0}
    pmcid = record["pmcid"]
    if not isinstance(pmcid, str) or not pmcid.startswith("PMC") or not pmcid[3:].isdigit():
        return {**base, "status": "invalid_pmcid"}
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
            return {**base, "status": "full_text_xml_available",
                    "xml_bytes": len(payload),
                    "article_sections": sum(1 for node in root.iter()
                                            if node.tag.split("}")[-1] == "sec")}
        except urllib.error.HTTPError as exc:
            if exc.code in (404, 403):
                return {**base, "status": "full_text_unavailable", "http_status": exc.code}
            if attempt == retries:
                return {**base, "status": "request_error", "http_status": exc.code}
        except (OSError, ValueError, TimeoutError):
            if attempt == retries:
                return {**base, "status": "request_error"}
        time.sleep(0.5 * 2 ** attempt)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--candidates", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--workers", type=int, default=8)
    args = p.parse_args()
    if not 1 <= args.workers <= 16:
        p.error("workers must be between 1 and 16")
    candidates = json.loads(Path(args.candidates).read_text(encoding="utf-8"))["records"]
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(check, candidates))
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
    Path(args.out).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"candidates": len(results), "statuses": counts}))

if __name__ == "__main__":
    main()
