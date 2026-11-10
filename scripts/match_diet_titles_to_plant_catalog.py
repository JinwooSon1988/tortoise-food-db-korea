#!/usr/bin/env python3
"""Bulk title-only botanical catalog hints. Never feeding or safety evidence."""
import argparse
import json
import re
from pathlib import Path
try:
    from scripts.join_botanical_mentions_to_public_plants import build_index, canonical
except ModuleNotFoundError:
    from join_botanical_mentions_to_public_plants import build_index, canonical

BINOMIAL = re.compile(r"\b([A-Z][a-z-]+\s+[a-z][a-z-]+)\b")

def match_titles(triage, plants):
    index = build_index(plants)
    rows = []
    for group in ("priority_review", "context_review"):
        for paper in triage.get("groups", {}).get(group, []):
            title = paper.get("title") or ""
            found = set()
            for name in BINOMIAL.findall(title):
                key = canonical(name)
                if not key or key not in index:
                    continue
                found.add((key, tuple(sorted(set(index[key])))))
            for name, ids in sorted(found):
                rows.append({"title": title, "doi": paper.get("doi"),
                             "source_key": paper.get("source_key"),
                             "candidate_plant_name": name,
                             "public_plant_id_candidates": list(ids),
                             "match_status": "exact_name_candidate" if len(ids) == 1 else "ambiguous_name",
                             "feeding_observation_status": "not_verified",
                             "feeding_safety_status": "unassessed",
                             "verified_plant_links": []})
    return {"title_leads_scanned": sum(len(triage.get("groups", {}).get(k, []))
            for k in ("priority_review", "context_review")),
            "candidate_matches": len(rows), "records": rows,
            "warning": "Title-only name co-occurrence; no evidence of ingestion or safety."}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--triage", required=True)
    p.add_argument("--plants", default="data/plants.json")
    p.add_argument("--out", required=True)
    args = p.parse_args()
    triage = json.loads(Path(args.triage).read_text(encoding="utf-8"))
    plants = json.loads(Path(args.plants).read_text(encoding="utf-8"))
    result = match_titles(triage, plants)
    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"scanned": result["title_leads_scanned"], "matches": result["candidate_matches"]}))

if __name__ == "__main__":
    main()
