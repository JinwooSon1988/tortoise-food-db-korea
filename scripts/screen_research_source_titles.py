#!/usr/bin/env python3
"""Deterministic, conservative title-only screening of unverified sources.

No plant-to-source match, ingestion, feeding suitability, or safety is inferred.
Run --check to detect changes to the saved screening results without writing.
"""
import argparse
import json
import pathlib
import re

TORTOISE = re.compile(r"\b(?:tortoises?|testudinidae|testudo|gopherus|geochelone|centrochelys|chelonoidis|stigmochelys|astrochelys|aldabrachelys|kinixys|manouria|indotestudo|agrionemys|homopus|psammobates|pyxis|chersina|xerobates)\b", re.I)
DIET = re.compile(r"\b(?:diet|dietary|feeding|foraging|food habits|food plants|food preferences|food selection|grazing|herbivory|herbivores?|frugivory|stomach contents|gut contents|fecal metabarcoding)\b", re.I)
NON_TORTOISE = re.compile(r"\b(?:tortoise beetles?|tortoiseshell|tortoise shell beetle)\b", re.I)

def build(queue):
    data = json.loads(pathlib.Path(queue).read_text(encoding="utf-8"))
    rows = []
    counts = {"tortoise_diet_title": 0, "tortoise_other_title": 0,
              "diet_other_taxon_title": 0, "other_title": 0}
    for row in data["records"]:
        title = (row.get("title") or "").replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
        title = re.sub(r"<[^>]*>", " ", title)
        animal = bool(TORTOISE.search(title)) and not bool(NON_TORTOISE.search(title))
        feeding = bool(DIET.search(title))
        tier = ("tortoise_diet_title" if animal and feeding else
                "tortoise_other_title" if animal else
                "diet_other_taxon_title" if feeding else "other_title")
        counts[tier] += 1
        rows.append({"source_url": row["source_url"], "title": row["title"],
                     "screening_tier": tier, "title_only": True,
                     "source_review_status": "not_reviewed",
                     "taxon_association_count": len(row["taxon_associations"]),
                     "feeding_safety_status": "unassessed"})
    return {"schema_version": "1.0",
            "method": "Conservative title-only animal and diet keyword screening. No full text or taxon association verified.",
            "counts": {"unique_sources": len(rows),
                       "source_taxon_links": sum(r["taxon_association_count"] for r in rows),
                       **counts},
            "records": rows}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", default="data/research_unique_source_review_queue.json")
    p.add_argument("--output", default="data/research_source_title_screening.json")
    p.add_argument("--check", action="store_true")
    args = p.parse_args()
    result = build(args.input)
    path = pathlib.Path(args.output)
    if args.check:
        saved = json.loads(path.read_text(encoding="utf-8"))
        if saved != result:
            raise SystemExit("FAIL: title screening differs from source review queue")
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps(result["counts"], ensure_ascii=False))

if __name__ == "__main__":
    main()
