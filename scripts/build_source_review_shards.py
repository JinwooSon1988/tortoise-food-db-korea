#!/usr/bin/env python3
"""Partition unique research sources into deterministic balanced review batches.

Source is the unit of work. All plant candidate links for a source stay together.
No title hit is promoted to feeding evidence or a safety assessment.
"""
import argparse
import json
from pathlib import Path

def partition(queue, screening, shards):
    if shards < 1:
        raise ValueError("shards must be positive")
    sources = queue["records"]
    screen = {r["source_url"]: r for r in screening["records"]}
    if len(screen) != len(sources):
        raise ValueError("screening/queue source counts differ")
    tiers = {"tortoise_diet_title": 0, "tortoise_other_title": 1,
             "diet_other_taxon_title": 2, "other_title": 3}
    batches = [{"id": i, "sources": [], "candidate_links": 0} for i in range(shards)]
    ordered = sorted(sources, key=lambda r: (
        tiers[screen[r["source_url"]]["screening_tier"]],
        -len(r["taxon_associations"]), r["source_url"]))
    # Assign each tier independently to the least-loaded batch; avoids one
    # batch receiving all high-priority sources and prevents duplicate work.
    for source in ordered:
        url = source["source_url"]
        if url not in screen:
            raise ValueError("queue source missing from screening: " + url)
        target = min(batches, key=lambda b: (b["candidate_links"], len(b["sources"]), b["id"]))
        target["sources"].append({
            "source_url": url, "title": source["title"],
            "screening_tier": screen[url]["screening_tier"],
            "source_review_status": "not_reviewed",
            "feeding_safety_status": "unassessed",
            "candidate_taxon_ids": [a["taxon_id"] for a in source["taxon_associations"]],
        })
        target["candidate_links"] += len(source["taxon_associations"])
    actual = [r["source_url"] for b in batches for r in b["sources"]]
    if len(actual) != len(set(actual)) or set(actual) != {r["source_url"] for r in sources}:
        raise ValueError("source missing or duplicated")
    if sum(b["candidate_links"] for b in batches) != queue["counts"]["source_taxon_links"]:
        raise ValueError("candidate links lost")
    return batches

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--queue", default="data/research_unique_source_review_queue.json")
    p.add_argument("--screening", default="data/research_source_title_screening.json")
    p.add_argument("--shards", type=int, default=64)
    p.add_argument("--out", default="/tmp/geobukbap-source-review")
    args = p.parse_args()
    queue = json.loads(Path(args.queue).read_text(encoding="utf-8"))
    screening = json.loads(Path(args.screening).read_text(encoding="utf-8"))
    batches = partition(queue, screening, args.shards)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    manifest = {"schema_version": "1.0", "warning": "Unverified research candidates only.",
                "total_sources": len(queue["records"]),
                "total_candidate_links": queue["counts"]["source_taxon_links"],
                "batches": []}
    for b in batches:
        filename = f"source_review_{b['id']:02d}.json"
        (out / filename).write_text(json.dumps({"schema_version": "1.0",
            "warning": "Unverified research candidates; no feeding safety conclusions.",
            "records": b["sources"]}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        manifest["batches"].append({"file": filename, "sources": len(b["sources"]),
                                    "candidate_links": b["candidate_links"]})
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"sources": manifest["total_sources"], "links": manifest["total_candidate_links"],
                      "batches": len(batches), "max_links_per_batch": max(b["candidate_links"] for b in batches)}))

if __name__ == "__main__":
    main()
