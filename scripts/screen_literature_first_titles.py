#!/usr/bin/env python3
"""Conservative, multilingual title triage for literature-first unreviewed leads."""
import argparse
import json
import re
from pathlib import Path

TORTOISE = re.compile(r"\b(?:tortoises?|testudo|centrochelys|stigmochelys|gopherus|chelonoidis|geochelone|tortugas?|tartarughe|tortues?)\b", re.I)
FOOD = re.compile(r"\b(?:diet|dietary|feeding|food|forag(?:ing|e)|nutrition|consumption|alimentaci[oó]n|dieta|alimentation|nourriture|nahrung|herbivor\w*|plant\w*|vegetation)\b", re.I)


def screen(data):
    if data.get("scope") != "literature_first_unreviewed_not_feeding_evidence":
        raise ValueError("unsupported source scope")
    candidates = []
    for work in data.get("works", []):
        if work.get("status") != "literature_lead_unreviewed" or work.get("feeding_confirmed") is not False:
            raise ValueError("invalid unreviewed evidence status")
        title = work.get("title") or ""
        if TORTOISE.search(title) and FOOD.search(title):
            candidates.append({
                "openalex_id": work["openalex_id"], "doi": work.get("doi"),
                "title": title, "year": work.get("year"),
                "source_url": work.get("source_url"),
                "query_matches": work.get("query_matches", []),
                "screening_status": "title_candidate_requires_abstract_and_fulltext_review",
                "feeding_confirmed": False,
            })
    return {"scope": "title_screen_not_feeding_evidence",
            "input_unique_works": len(data.get("works", [])),
            "title_candidates": len(candidates),
            "feeding_verdicts_confirmed": 0,
            "candidates": candidates}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = screen(json.loads(args.input.read_text(encoding="utf-8")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("input_unique_works", "title_candidates", "feeding_verdicts_confirmed")}))


if __name__ == "__main__":
    main()
