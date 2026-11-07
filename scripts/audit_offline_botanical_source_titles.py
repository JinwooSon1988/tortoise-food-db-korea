#!/usr/bin/env python3
"""Join offline botanical review pairs to previously fetched source metadata.

Title relevance is a review-routing signal only, never feeding or safety proof.
This script makes no network calls and supports replay during provider outages.
"""
import argparse
import json
import re
from pathlib import Path

TORTOISE = re.compile(r"\b(?:tortoises?|Testudo|Gopherus|Chelonoidis|Geochelone|Stigmochelys|Centrochelys|Kinixys|Aldabrachelys|Astrochelys|Indotestudo|Manouria|Psammobates|Pyxis|Homopus)\b", re.I)
DIET = re.compile(r"\b(?:diet|diets|food|feeding|forag(?:e|ing)|grazing|herbivor(?:e|y|ous)|consum(?:e|ption)|browse|frugivor(?:e|y)|plant selection)\b", re.I)

def audit(discovery, prioritized):
    metadata = {r["source_url"]: r for r in discovery["records"]}
    rows = []
    for row in prioritized["records"]:
        meta = metadata.get(row["source_url"], {})
        title = meta.get("title") or meta.get("queue_title") or ""
        t = bool(TORTOISE.search(title)) and not bool(re.search(r"\btortoise beetles?\b", title, re.I))
        d = bool(DIET.search(title))
        signal = "tortoise_diet_title" if t and d else "tortoise_title" if t else "other_title"
        rows.append({
            "candidate_plant_name": row["candidate_plant_name"],
            "source_url": row["source_url"],
            "source_title": title,
            "title_review_signal": signal,
            "mention_count": row["mention_count"],
            "public_plant_id_candidates": row["public_plant_id_candidates"],
            "review_status": "not_reviewed",
            "feeding_observation_status": "not_verified",
            "feeding_safety_status": "unassessed",
            "verified_plant_links": [],
        })
    priority = {"tortoise_diet_title": 0, "tortoise_title": 1, "other_title": 2}
    rows.sort(key=lambda r: (priority[r["title_review_signal"]], -r["mention_count"],
                             r["candidate_plant_name"], r["source_url"]))
    return {"schema_version": "1.0",
            "warning": "Title signals are unverified review leads, not ingestion or safety evidence.",
            "review_pairs": len(rows),
            "signal_counts": {key: sum(r["title_review_signal"] == key for r in rows) for key in priority},
            "records": rows}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--discovery", required=True)
    parser.add_argument("--prioritized", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    discovery = json.loads(Path(args.discovery).read_text(encoding="utf-8"))
    prioritized = json.loads(Path(args.prioritized).read_text(encoding="utf-8"))
    result = audit(discovery, prioritized)
    assert all(not r["verified_plant_links"] and r["feeding_safety_status"] == "unassessed"
               for r in result["records"])
    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["signal_counts"]))

if __name__ == "__main__":
    main()
