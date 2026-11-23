#!/usr/bin/env python3
"""Consolidate manually triaged publication-plant evidence into a species review queue.

This never infers feeding or safety from abstract context.
"""
import argparse
import csv
from pathlib import Path

PRIORITY = {
    "clinical_adverse_event_abstract": 1,
    "experimental_diet_or_nutrition_abstract": 2,
    "diet_or_seed_dispersal_abstract": 3,
    "indirect_seed_dispersal_or_preference_context": 4,
    "non_target_or_aquatic_turtle_context": 5,
    "habitat_vegetation_or_unrelated_context": 6,
}


def consolidate(rows):
    groups = {}
    for row in rows:
        name = row.get("candidate_binomial", "").strip()
        paper = row.get("openalex_id", "").strip()
        category = row.get("abstract_context_bucket", "")
        if not name or not paper.startswith("https://openalex.org/W") or category not in PRIORITY:
            continue
        group = groups.setdefault(name.casefold(), {"name": name, "papers": set(), "pairs": set(),
                                                       "categories": set(), "examples": []})
        group["papers"].add(paper)
        group["pairs"].add((paper, name.casefold()))
        group["categories"].add(category)
        group["examples"].append((PRIORITY[category], paper, row.get("sample_context", "")))
    output = []
    for group in groups.values():
        example = sorted(group["examples"])[0]
        output.append({
            "candidate_binomial": group["name"],
            "unique_papers": len(group["papers"]),
            "unique_paper_plant_pairs": len(group["pairs"]),
            "review_priority": example[0],
            "context_categories": " | ".join(sorted(group["categories"], key=lambda x: PRIORITY[x])),
            "openalex_papers": " | ".join(sorted(group["papers"])),
            "priority_context": example[2],
            "taxonomy_review": "required",
            "full_text_checked": "no",
            "tortoise_species_verified": "no",
            "plant_part_verified": "no",
            "feeding_confirmed": "no_full_text_verification",
            "safety_verdict": "not_assessed",
        })
    return sorted(output, key=lambda x: (x["review_priority"], -x["unique_papers"], x["candidate_binomial"]))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("input", type=Path)
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    if args.input.resolve() == args.output.resolve():
        p.error("input and output must differ")
    with args.input.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    output = consolidate(rows)
    if not output:
        p.error("no valid records")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(output[0]))
        writer.writeheader()
        writer.writerows(output)
    print(f"unique_species_candidates={len(output)} priority_1_to_3={sum(x['review_priority'] <= 3 for x in output)}")


if __name__ == "__main__":
    main()
