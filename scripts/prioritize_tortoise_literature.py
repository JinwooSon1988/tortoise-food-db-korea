#!/usr/bin/env python3
"""Reproducible title-only prioritization; never infer tortoise feeding safety."""
import argparse
import csv
import re
from pathlib import Path

TORTOISE = re.compile(r"\b(?:testudo|gopherus|chelonoidis|centrochelys|stigmochelys|tortoises?|tortuga mora|tartarughe)\b", re.I)
FOOD = re.compile(r"\b(?:diet|dietary|food|feeding|forag\w*|alimentation|alimentaci[oó]n|dieta|nutritive|nutrition|herbivor\w*|nourriture)\b", re.I)
DIRECT = re.compile(r"\b(?:diet|food habits|food choice|food preference|feeding ecology|feeding behaviour|plants? consumed|plants? eaten|food plants|foraging ecology|alimentation|alimentaci[oó]n|dieta)\b", re.I)
NEGATIVE = re.compile(r"\b(?:eagles?|coyotes?|predat\w*|fecal microbiota|urolithiasis|intraoral food transport)\b", re.I)


def prioritize(rows):
    output = []
    seen = set()
    for row in rows:
        identifier = row.get("openalex_id", "").strip()
        if not identifier or identifier in seen:
            continue
        seen.add(identifier)
        title = row.get("title") or ""
        score = 4 * bool(TORTOISE.search(title)) + 3 * bool(FOOD.search(title)) + 3 * bool(DIRECT.search(title)) - 5 * bool(NEGATIVE.search(title))
        output.append({**row, "title_priority_score": score,
                       "triage_bucket": "high_title_priority" if score >= 10 else "review_title" if score >= 7 else "background_or_low_relevance",
                       "triage_basis": "automated_title_keywords_only_not_abstract_or_fulltext",
                       "feeding_verdict": "unverified"})
    return sorted(output, key=lambda r: (-r["title_priority_score"], (r.get("title") or "").casefold()))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("input", type=Path)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    if args.input.resolve() == args.output.resolve():
        p.error("input and output must differ")
    with args.input.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    ranked = prioritize(rows)
    if not ranked:
        p.error("no valid OpenAlex identifiers")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(ranked[0]))
        writer.writeheader()
        writer.writerows(ranked)
    print(f"ranked_unique_works={len(ranked)}")


if __name__ == "__main__":
    main()
