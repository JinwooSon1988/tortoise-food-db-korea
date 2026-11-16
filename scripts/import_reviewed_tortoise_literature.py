#!/usr/bin/env python3
"""Import human-reviewed literature observations into *unverified* evidence leads."""
import argparse
import csv
import json
import re
from pathlib import Path

from scripts.stage_feeding_evidence_leads import validate

BINOMIAL = re.compile(r"^[A-Z][a-z]+ [a-z][a-z-]+(?: [a-z][a-z-]+)?$")
ALLOWED_OBSERVATIONS = {"observed_ingestion", "dietary_analysis", "feeding_trial"}


def convert(input_path, output_path):
    if input_path.resolve() == output_path.resolve() or output_path.exists():
        raise ValueError("output must be new and distinct")
    converted = []
    seen = set()
    with input_path.open(encoding="utf-8-sig", newline="") as stream:
        for number, row in enumerate(csv.DictReader(stream), 2):
            if row.get("review_status") != "reviewed_observation":
                continue
            plant = (row.get("verified_plant_scientific_name") or "").strip()
            tortoise = (row.get("verified_tortoise_scientific_name") or "").strip()
            quote = (row.get("evidence_quote") or "").strip()
            observation = (row.get("observation_type") or "").strip()
            title = (row.get("source_title") or "").strip()
            reviewer = (row.get("reviewer_notes") or "").strip()
            if not BINOMIAL.fullmatch(plant) or not BINOMIAL.fullmatch(tortoise):
                raise ValueError(f"row {number}: reviewer must verify plant and tortoise binomials")
            if observation not in ALLOWED_OBSERVATIONS or len(quote) < 20 or not reviewer or not title:
                raise ValueError(f"row {number}: missing observation type, quote, title or reviewer notes")
            source_id = (row.get("source_record_id") or "").strip()
            database = (row.get("source_database") or "").strip()
            if not source_id or not database:
                raise ValueError(f"row {number}: missing literature identity")
            item = validate({
                "plant_scientific_name": plant,
                "plant_part": (row.get("verified_plant_part") or "").strip() or None,
                "tortoise_scientific_name": tortoise,
                "source_url": row.get("source_url"),
                "source_type": "peer_reviewed",
                "source_title": title,
                "source_identifier": f"{database}:{source_id}",
                "observed_at": row.get("reviewed_at")})
            item["observation_type"] = observation
            item["evidence_quote"] = quote
            item["reviewer_notes"] = reviewer
            item["review_status"] = "reviewed_observation_unverified_for_publication"
            key = (item["source_identifier"], plant, tortoise, item["plant_part"], observation)
            if key in seen:
                raise ValueError(f"row {number}: duplicate reviewed observation")
            seen.add(key)
            converted.append(item)
    if not converted:
        raise ValueError("no explicitly reviewed observations; refusing empty output")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("x", encoding="utf-8") as stream:
        for row in converted:
            stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    return {"reviewed_observation_leads": len(converted), "public_feeding_verdicts": 0}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(convert(args.input, args.output), sort_keys=True))
