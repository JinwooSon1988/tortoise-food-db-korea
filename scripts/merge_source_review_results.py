#!/usr/bin/env python3
"""Fail-closed merge of independently reviewed source-first research batches.

This tool NEVER publishes plant safety assessments. It only merges source-level
review outcomes and retains explicit evidence for each verified plant link.
"""
import argparse
import json
from pathlib import Path

ALLOWED = {"pending", "excluded_irrelevant", "context_reviewed", "plant_links_reviewed"}
def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def merge(queue, files):
    expected = {r["source_url"]: {a["taxon_id"] for a in r["taxon_associations"]}
                for r in queue["records"]}
    output = {}
    for file in sorted(files):
        for row in load(file)["records"]:
            url = row["source_url"]
            if url not in expected:
                raise ValueError("Unknown source: " + url)
            if url in output:
                raise ValueError("Duplicate source across batches: " + url)
            status = row.get("review_status")
            if status not in ALLOWED:
                raise ValueError("Invalid review status: " + url)
            if row.get("feeding_safety_status") != "unassessed":
                raise ValueError("Safety assessment prohibited in research merge: " + url)
            verified = row.get("verified_plant_links", [])
            if not isinstance(verified, list):
                raise ValueError("verified_plant_links must be an array: " + url)
            seen = set()
            for link in verified:
                taxon = link.get("taxon_id")
                if taxon not in expected[url] or taxon in seen:
                    raise ValueError("Unknown or duplicated taxon association: " + url)
                seen.add(taxon)
                if not all(isinstance(link.get(k), str) and link[k].strip()
                           for k in ("verbatim_plant_name", "evidence_locator",
                                     "observed_animal_taxon", "observed_plant_part")):
                    raise ValueError("Incomplete plant-link provenance: " + url)
                if link.get("feeding_safety_status") not in (None, "unassessed"):
                    raise ValueError("Plant-link safety promotion prohibited: " + url)
            if verified and status != "plant_links_reviewed":
                raise ValueError("Verified links require plant_links_reviewed: " + url)
            if status == "plant_links_reviewed" and not verified:
                raise ValueError("plant_links_reviewed requires verified links: " + url)
            if status == "excluded_irrelevant" and verified:
                raise ValueError("Irrelevant source cannot have verified links: " + url)
            output[url] = row
    return {"schema_version": "1.0", "scope": "research review only; no feeding safety decisions",
            "sources_reviewed": len(output),
            "plant_links_verified": sum(len(r.get("verified_plant_links", [])) for r in output.values()),
            "records": [output[k] for k in sorted(output)]}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--queue", default="data/research_unique_source_review_queue.json")
    p.add_argument("--out", required=True)
    p.add_argument("reviews", nargs="+")
    args = p.parse_args()
    result = merge(load(args.queue), args.reviews)
    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"sources_reviewed": result["sources_reviewed"],
                      "plant_links_verified": result["plant_links_verified"]}))

if __name__ == "__main__":
    main()
