#!/usr/bin/env python3
"""Prioritize catalog-linked botanical mentions for human source review.

This is a deterministic review queue, NOT a feeding observation or safety claim.
"""
import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

# Search cues prioritize manual review only; never establish ingestion or safety.
FEEDING_CUES = re.compile(r"\b(?:eat|eats|eaten|feeding|fed|forage|foraging|browse|browsing|grazing|ingest|ingested|consume|consumed|consumption|diet|diets|bite|bites)\b", re.I)
TORTOISE_CUES = re.compile(r"\b(?:tortoises?|Testudo|Gopherus|Chelonoidis|Geochelone|Stigmochelys|Centrochelys|Kinixys|Aldabrachelys|Astrochelys|Indotestudo|Manouria|Psammobates|Pyxis|Homopus)\b", re.I)

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
        # Score every mention, not only the first five. Keep the most relevant
        # excerpts for review and require co-occurrence within one excerpt.
        def cues(row):
            context = row["exact_context_excerpt"]
            feeding = bool(FEEDING_CUES.search(context))
            tortoise = bool(TORTOISE_CUES.search(context)) and not bool(
                re.search(r"\btortoise beetles?\b", context, re.I))
            return feeding, tortoise
        scored = [(r, *cues(r)) for r in rows]
        feeding_context_count = sum(feeding for _, feeding, _ in scored)
        tortoise_context_count = sum(tortoise for _, _, tortoise in scored)
        combined_context_count = sum(feeding and tortoise for _, feeding, tortoise in scored)
        ranked = sorted(scored, key=lambda item: (
            -int(item[1] and item[2]), -int(item[2]), -int(item[1]),
            str(item[0].get("source_element_id") or ""),
            int(item[0].get("name_start_offset") or 0)))
        output.append({
            "candidate_plant_name": name,
            "source_url": url,
            "pmcid": rows[0]["pmcid"],
            "public_plant_id_candidates": ids,
            "match_status": rows[0]["match_status"],
            "mention_count": len(rows),
            "feeding_keyword_contexts": feeding_context_count,
            "tortoise_keyword_contexts": tortoise_context_count,
            "combined_keyword_contexts": combined_context_count,
            "review_priority_signal": "tortoise_and_feeding_keywords" if combined_context_count else ("tortoise_keyword" if tortoise_context_count else ("feeding_keyword" if feeding_context_count else "no_keyword_signal")),
            "review_priority_is_evidence": False,
            "contexts": [{
                "source_element_id": r.get("source_element_id"),
                "name_start_offset": r.get("name_start_offset"),
                "exact_context_excerpt": r["exact_context_excerpt"]
            } for r, _, _ in ranked[:5]],
            "contexts_omitted": max(0, len(rows)-5),
            "review_status": "not_reviewed",
            "feeding_observation_status": "not_verified",
            "feeding_safety_status": "unassessed",
            "verified_plant_links": []
        })
    output.sort(key=lambda r: ({"tortoise_and_feeding_keywords":0, "tortoise_keyword":1, "feeding_keyword":2, "no_keyword_signal":3}[r["review_priority_signal"]],
                               r["match_status"] != "exact_name_candidate",
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
