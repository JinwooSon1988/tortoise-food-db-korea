#!/usr/bin/env python3
"""Batch extract review-only plant mentions from OpenAlex abstracts.

This script deliberately does NOT classify organisms or infer actual feeding.
Every candidate needs taxonomic and source-context review.
"""
import argparse
import csv
import json
import re
from pathlib import Path

BINOMIAL = re.compile(r"\b([A-Z][a-z]{2,})\s+([a-z]{3,})(?![a-z])\b")
FEEDING = re.compile(r"\b(?:eat(?:s|en|ing)?|consum(?:e|ed|es|ing)|feed(?:s|ing)?|fed|diet(?:ary)?|forag(?:e|ed|es|ing)|ingest(?:ed|ion|ing)?|graz(?:e|ed|ing)|digestib(?:le|ility))\b", re.I)
NEGATION = re.compile(r"\b(?:not|never|no|without|avoid(?:s|ed|ing)?|refus(?:e|ed|es|ing))\b", re.I)


def extract(records, context_chars=180):
    if context_chars < 40:
        raise ValueError("context window too short")
    output = []
    seen = set()
    for record in records:
        identifier = record.get("openalex_id")
        abstract = record.get("abstract")
        if not isinstance(identifier, str) or not identifier.startswith("https://openalex.org/W"):
            continue
        if not isinstance(abstract, str) or not abstract.strip():
            continue
        for match in BINOMIAL.finditer(abstract):
            candidate = match.group(0)
            left = max(0, match.start() - context_chars)
            right = min(len(abstract), match.end() + context_chars)
            window = abstract[left:right]
            key = (identifier, candidate.casefold(), match.start())
            if key in seen:
                continue
            seen.add(key)
            output.append({
                "openalex_id": identifier,
                "candidate_binomial": candidate,
                "context": window,
                "feeding_keyword_nearby": bool(FEEDING.search(window)),
                "negation_keyword_nearby": bool(NEGATION.search(window)),
                "taxonomic_identity": "unverified",
                "feeding_event": "unverified",
                "tortoise_species": "unverified",
                "plant_part": "unverified",
                "safety_verdict": "not_assessed",
                "evidence_status": "abstract_string_candidate_only",
            })
    return sorted(output, key=lambda x: (not x["feeding_keyword_nearby"], x["openalex_id"], x["candidate_binomial"]))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("input", type=Path, help="JSON from enrich_openalex_abstracts.py")
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    if args.input.resolve() == args.output.resolve():
        p.error("input and output must differ")
    data = json.loads(args.input.read_text(encoding="utf-8"))
    if data.get("scope") != "research_only_unreviewed_abstracts":
        p.error("unsupported evidence scope")
    rows = extract(data["records"])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    columns = ["openalex_id", "candidate_binomial", "context", "feeding_keyword_nearby",
               "negation_keyword_nearby", "taxonomic_identity", "feeding_event",
               "tortoise_species", "plant_part", "safety_verdict", "evidence_status"]
    with args.output.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps({"abstract_candidates": len(rows),
                      "keyword_context_candidates": sum(x["feeding_keyword_nearby"] for x in rows),
                      "confirmed_feeding_events": 0, "safety_verdicts": 0}))


if __name__ == "__main__":
    main()
