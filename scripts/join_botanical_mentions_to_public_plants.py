#!/usr/bin/env python3
"""Bulk exact scientific-name matching of unverified mentions to public plants.

A name match is a review lead, never evidence of ingestion or feeding safety.
"""
import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

def canonical(name):
    return " ".join(re.findall(r"[a-z]+", str(name).casefold()))

def build_index(plants):
    index = defaultdict(list)
    for plant in plants:
        name = plant.get("scientific", "")
        if name and len(canonical(name).split()) >= 2:
            index[canonical(name)].append(plant["id"])
    return index

def join(mentions, plants):
    index = build_index(plants)
    rows = []
    for mention in mentions:
        name = mention["candidate_plant_name"]
        ids = index.get(canonical(name), [])
        rows.append({
            "source_url": mention["source_url"],
            "pmcid": mention["pmcid"],
            "candidate_plant_name": name,
            "source_element_id": mention.get("source_element_id"),
            "name_start_offset": mention.get("name_start_offset"),
            "name_end_offset": mention.get("name_end_offset"),
            "exact_context_excerpt": mention["exact_context_excerpt"],
            "public_plant_id_candidates": ids,
            "match_status": "exact_name_candidate" if len(ids) == 1 else
                            "ambiguous_name" if ids else "no_exact_name_match",
            "feeding_observation_status": "not_verified",
            "feeding_safety_status": "unassessed",
            "verified_plant_links": []})
    return rows

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mentions", required=True)
    parser.add_argument("--plants", default="data/plants.json")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    data = json.loads(Path(args.mentions).read_text(encoding="utf-8"))
    plants = json.loads(Path(args.plants).read_text(encoding="utf-8"))
    rows = join(data["candidates"], plants)
    counts = {}
    for row in rows:
        key = row["match_status"]
        counts[key] = counts.get(key, 0) + 1
    assert len(rows) == data["candidate_mentions"]
    assert all(r["feeding_observation_status"] == "not_verified" and
               r["feeding_safety_status"] == "unassessed" and
               not r["verified_plant_links"] for r in rows)
    output = {"schema_version": "1.0", "warning": "Name matches are unverified review leads only.",
              "total_mentions": len(rows), "match_counts": counts, "records": rows}
    Path(args.out).write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"mentions": len(rows), "matches": counts}))

if __name__ == "__main__":
    main()
