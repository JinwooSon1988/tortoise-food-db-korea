#!/usr/bin/env python3
"""Conservative title triage of unreviewed OpenAlex hits; never asserts feeding safety."""
import argparse
import json
import re
from pathlib import Path

TORTOISE = re.compile(r"\b(?:tortoises?|testudo|geochelone|centrochelys|stigmochelys|astrochelys|chelonoidis|gopherus|agrionemys|malacochersus)\b", re.I)
DIET = re.compile(r"\b(?:diet|dietary|feeding|feed|food|foraging|forage|consumption|consume|nutrition|ingestion|eating)\b", re.I)


def screen(path):
    works = {}
    with path.open(encoding="utf-8") as stream:
        for number, line in enumerate(stream, 1):
            try:
                row = json.loads(line)
            except ValueError as exc:
                raise ValueError(f"invalid JSON row {number}") from exc
            if row.get("status") not in ("searched", "retry_needed") or not isinstance(row.get("hits"), list):
                raise ValueError(f"invalid checkpoint row {number}")
            for hit in row["hits"]:
                if not isinstance(hit, dict) or hit.get("status") != "literature_lead_unreviewed":
                    raise ValueError(f"unreviewed lead status violated at row {number}")
                key = hit.get("openalex_id") or hit.get("doi")
                if not isinstance(key, str) or not key.strip():
                    raise ValueError(f"missing literature identifier at row {number}")
                if key not in works:
                    works[key] = {"title": hit.get("title") or "", "plant_names": set()}
                works[key]["plant_names"].add(row.get("name", ""))
    candidates = []
    for key, work in sorted(works.items()):
        title = work["title"]
        if TORTOISE.search(title):
            candidates.append({"id": key, "title": title,
                               "plant_names": sorted(work["plant_names"]),
                               "diet_term_in_title": bool(DIET.search(title)),
                               "feeding_confirmed": False})
    return {"scope": "title_screen_only_not_feeding_evidence",
            "unique_works": len(works),
            "tortoise_title_candidates": len(candidates),
            "tortoise_and_diet_title_candidates": sum(x["diet_term_in_title"] for x in candidates),
            "feeding_verdicts_confirmed": 0,
            "candidates_for_manual_abstract_review": candidates}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = json.dumps(screen(args.input), ensure_ascii=False, indent=2) + "\n"
    if args.output:
        if args.input.resolve() == args.output.resolve():
            parser.error("output must not overwrite input")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(result, encoding="utf-8")
    print(result, end="")
