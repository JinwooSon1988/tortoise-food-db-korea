#!/usr/bin/env python3
"""Generate reviewable, source-located botanical mentions from Europe PMC JATS.

Mentions are candidates only. No claim that a tortoise consumed the plant.
No feeding safety assessment, no automatic public publication.
"""
import argparse
import concurrent.futures
import json
import re
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

BINOMIAL = re.compile(r"\b([A-Z][a-z]{2,}\s+[a-z][a-z-]{2,})\b")
SKIP_GENUS = {"Table", "Figure", "Supplementary", "Materials", "Results", "Discussion",
              "Methods", "Data", "Desert", "Gopher", "Eastern", "Western", "North",
              "South", "United", "New", "Great", "Food", "Plant", "Species",
              "The", "This", "These", "Those", "Some", "Many", "Most", "Each",
              "Their", "There", "They", "Our", "All", "Both", "Other", "Several",
              "Recorded"}

def candidates_from_xml(xml, source_url, pmcid):
    root = ET.fromstring(xml)
    if root.tag.split("}")[-1] != "article":
        raise ValueError("Not JATS article")
    rows = []
    parents = {child: parent for parent in root.iter() for child in parent}
    for node in root.iter():
        tag = node.tag.split("}")[-1]
        if tag not in ("p", "caption", "td", "th"):
            continue
        # JATS permits nested paragraphs in captions and table cells. Scan the
        # outer element once rather than counting the same text twice.
        parent = parents.get(node)
        nested_in_scanned_element = False
        while parent is not None:
            if parent.tag.split("}")[-1] in ("caption", "td", "th"):
                nested_in_scanned_element = True
                break
            parent = parents.get(parent)
        if nested_in_scanned_element:
            continue
        text = " ".join(" ".join(node.itertext()).split())
        if not text:
            continue
        section_id = node.get("id")
        # Preserve every occurrence and its original offset. A repeated name
        # in one paragraph may describe distinct observations or contexts.
        for match in BINOMIAL.finditer(text):
            name = match.group(1)
            if name.split()[0] in SKIP_GENUS:
                continue
            rows.append({
                "source_url": source_url, "pmcid": pmcid,
                "candidate_plant_name": name,
                "source_element": tag, "source_element_id": section_id,
                "exact_context_excerpt": text[max(0, match.start()-180):min(len(text), match.end()+180)],
                "name_start_offset": match.start(),
                "name_end_offset": match.end(),
                "context_truncated": match.start() > 180 or match.end()+180 < len(text),
                "identification_status": "unverified_name_mention",
                "feeding_observation_status": "not_verified",
                "feeding_safety_status": "unassessed",
                "verified_plant_links": []})
    return rows

def scan(record):
    pmcid = record["pmcid"]
    endpoint = "https://www.ebi.ac.uk/europepmc/webservices/rest/" + pmcid + "/fullTextXML"
    if cache_dir is not None:
        cached = Path(cache_dir) / (pmcid + ".xml")
        if cached.is_file():
            try:
                data = cached.read_bytes()
                if len(data) > 12_000_000:
                    return {"pmcid": pmcid, "status": "oversize", "attempts": 0, "candidates": []}
                return {"pmcid": pmcid, "status": "scanned", "attempts": 0,
                        "candidates": candidates_from_xml(data, record["source_url"], pmcid)}
            except (OSError, ET.ParseError, ValueError):
                pass  # Fall back to the existing bounded network retrieval.
    last_status = "unavailable_or_invalid"
    for attempt in range(3):
        try:
            req = urllib.request.Request(endpoint, headers={"User-Agent": "GeobukbapResearchReview/1.0"})
            with urllib.request.urlopen(req, timeout=25) as response:
                data = response.read(12_000_001)
            if len(data) > 12_000_000:
                return {"pmcid": pmcid, "status": "oversize", "attempts": attempt + 1, "candidates": []}
            return {"pmcid": pmcid, "status": "scanned", "attempts": attempt + 1,
                    "candidates": candidates_from_xml(data, record["source_url"], pmcid)}
        except urllib.error.HTTPError as exc:
            last_status = "http_" + str(exc.code)
            if exc.code not in (408, 429, 500, 502, 503, 504):
                break
        except (OSError, TimeoutError):
            last_status = "network_error"
        except (ET.ParseError, ValueError):
            last_status = "invalid_xml"
            break
        if attempt < 2:
            time.sleep(0.5 * (2 ** attempt))
    return {"pmcid": pmcid, "status": last_status, "attempts": attempt + 1, "candidates": []}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--fulltext-availability", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--workers", type=int, default=6)
    p.add_argument("--cache-dir", help="Reuse validated PMC XML from the availability stage")
    args = p.parse_args()
    if not 1 <= args.workers <= 12:
        p.error("workers must be 1..12")
    data = json.loads(Path(args.fulltext_availability).read_text(encoding="utf-8"))
    records = [r for r in data["records"] if r["status"] == "full_text_xml_available"]
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        scanned = list(pool.map(lambda record: scan(record, cache_dir=args.cache_dir), records))
    candidates = [c for r in scanned for c in r["candidates"]]
    assert all(c["feeding_observation_status"] == "not_verified" and
               c["feeding_safety_status"] == "unassessed" and
               c["verified_plant_links"] == [] for c in candidates)
    failures = [r for r in scanned if r["status"] != "scanned"]
    output = {"schema_version": "1.0",
              "warning": "Automated name mentions only. NOT evidence of ingestion or safety.",
              "sources_attempted": len(records),
              "sources_scanned": sum(r["status"] == "scanned" for r in scanned),
              "sources_failed": len(failures),
              "failed_sources": [{"pmcid": r["pmcid"], "status": r["status"], "attempts": r["attempts"]} for r in failures],
              "candidate_mentions": len(candidates),
              "source_results": [{k:v for k,v in r.items() if k != "candidates"} for r in scanned],
              "candidates": candidates}
    Path(args.out).write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"sources": len(records), "scanned": output["sources_scanned"],
                      "candidate_mentions": len(candidates)}))

if __name__ == "__main__":
    main()
