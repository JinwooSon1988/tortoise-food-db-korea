#!/usr/bin/env python3
"""Prioritize full-text botanical mentions for human review; never infer feeding safety."""
import argparse
import csv
import json
import re
from pathlib import Path

FEEDING = re.compile(r"\b(?:fed|feed(?:ing|s)?|forag(?:e|ed|ing)|graz(?:e|ed|ing)|consum(?:e|ed|ing)|ingest(?:ed|ion|ing)|diet(?:ary)?|stomach contents|fecal|faecal)\b", re.I)
NEGATION = re.compile(r"\b(?:not|no|never|without|avoid(?:ed)?|refus(?:e|ed|al)|toxic|poison(?:ous|ing)?)\b", re.I)
ANIMALS = re.compile(r"\b(?:tortoises?|Testudo|Geochelone|Centrochelys|Chelonoidis|Gopherus|Astrochelys|Aldabrachelys|Stigmochelys|Kinixys|Malacochersus|Homopus|Psammobates|Chersina|Indotestudo|Manouria)\b", re.I)


def triage(source, output, report):
    paths = [source, output, report]
    if len({p.resolve() for p in paths}) != 3 or output.exists() or report.exists():
        raise ValueError("distinct paths and new outputs required")
    rows, seen = [], set()
    with source.open(encoding="utf-8") as stream:
        for number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            item = json.loads(line)
            if item.get("review_status") != "unverified_fulltext_mention" or item.get("feeding_verdict") is not None:
                raise ValueError(f"unverified fulltext required at line {number}")
            key = (item.get("source_database"), str(item.get("source_record_id") or ""), item.get("plant_scientific_name"))
            if not all(key) or key in seen:
                raise ValueError(f"duplicate/missing identity at line {number}")
            seen.add(key)
            context = item.get("mention_context")
            if not isinstance(context, str) or not context.strip():
                raise ValueError(f"missing source context at line {number}")
            signals = {
                "feeding_language": bool(FEEDING.search(context)),
                "tortoise_language": bool(ANIMALS.search(context)),
                "negation_or_hazard_language": bool(NEGATION.search(context)),
            }
            score = 2 * int(signals["feeding_language"]) + 2 * int(signals["tortoise_language"]) - int(signals["negation_or_hazard_language"])
            rows.append({**item, "triage_score": score, "triage_signals": signals,
                         "review_status": "unverified_fulltext_mention",
                         "feeding_verdict": None,
                         "triage_note": "Keyword proximity for reviewer prioritization only; not evidence of feeding, suitability or safety."})
    if not seen:
        raise ValueError("empty review candidates")
    rows.sort(key=lambda r: (-r["triage_score"], r["plant_scientific_name"], r["source_database"], str(r["source_record_id"])))
    output.parent.mkdir(parents=True, exist_ok=True)
    report.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    with report.open("x", encoding="utf-8") as stream:
        json.dump({"candidates": len(rows),
                   "with_feeding_language": sum(r["triage_signals"]["feeding_language"] for r in rows),
                   "with_tortoise_language": sum(r["triage_signals"]["tortoise_language"] for r in rows),
                   "with_both": sum(r["triage_signals"]["feeding_language"] and r["triage_signals"]["tortoise_language"] for r in rows),
                   "status": "unverified_review_priority_only"}, stream, indent=2)
        stream.write("\n")
    return len(rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps({"triaged": triage(args.source, args.output, args.report)}))
