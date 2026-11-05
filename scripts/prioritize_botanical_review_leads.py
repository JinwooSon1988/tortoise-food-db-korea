#!/usr/bin/env python3
"""Prioritize catalog-linked botanical mentions for human source review.

This is a deterministic review queue, NOT a feeding observation or safety claim.
"""
import argparse
import json
from collections import defaultdict
from pathlib import Path

def prioritize(data):
    groups = defaultdict(list)
    for row in data["records"]:
        if row["match_status"] not in ("exact_name_candidate", "ambiguous_name"):
            continue
        key = (row["candidate_plant_name"], row["source_url"])
        groups[key].append(row)
    output = []
    for (name, url), rows in groups.items():
        ids = sorted(set(i for r in rows for i in r["public_plant_id_candidates"]))
        output.append({
            "candidate_plant_name": name,
            "source_url": url,
            "pmcid": rows[0]["pmcid"],
            "public_plant_id_candidates": ids,
            "match_status": rows[0]["match_status"],
            "mention_count": len(rows),
            "contexts": [{
                "source_element_id": r.get("source_element_id"),
                "name_start_offset": r.get("name_start_offset"),
                "exact_context_excerpt": r["exact_context_excerpt"]
            } for r in rows[:5]],
            "contexts_omitted": max(0, len(rows)-5),
            "review_status": "not_reviewed",
            "feeding_observation_status": "not_verified",
            "feeding_safety_status": "unassessed",
            "verified_plant_links": []
        })
    output.sort(key=lambda r: (r["match_status"] != "exact_name_candidate",
                               -r["mention_count"], r["candidate_plant_name"], r["source_url"]))
    return {"schema_version":"1.0",
            "warning":"Source/name review leads only. No ingestion or safety verified.",
            "total_mentions": data["total_mentions"],
            "review_pairs":len(output),
            "unique_names":len(set(r["candidate_plant_name"] for r in output)),
            "unique_sources":len(set(r["source_url"] for r in output)),
            "records":output}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--joined",required=True)
    parser.add_argument("--out",required=True)
    args=parser.parse_args()
    data=json.loads(Path(args.joined).read_text(encoding="utf-8"))
    result=prioritize(data)
    assert all(not r["verified_plant_links"] and r["feeding_safety_status"]=="unassessed" for r in result["records"])
    Path(args.out).write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:result[k] for k in ("review_pairs","unique_names","unique_sources")}))

if __name__=="__main__":
    main()
