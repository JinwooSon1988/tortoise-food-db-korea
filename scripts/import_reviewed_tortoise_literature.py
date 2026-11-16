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


def load_source_corpus(path):
    corpus = {}
    with path.open(encoding="utf-8") as stream:
        for number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            item = json.loads(line)
            key = (item.get("source_database"), str(item.get("source_record_id") or ""))
            if not all(key) or key in corpus:
                raise ValueError(f"source corpus duplicate/missing identity at line {number}")
            corpus[key] = item
    if not corpus:
        raise ValueError("empty source corpus")
    return corpus


def normalize_quote(value):
    return " ".join(re.sub(r"<[^>]*>", " ", value).split()).casefold()


def convert(input_path, output_path, source_corpus_path):
    corpus = load_source_corpus(source_corpus_path)
    if len({p.resolve() for p in (input_path, output_path, source_corpus_path)}) != 3 or output_path.exists():
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
            original = corpus.get((database, source_id))
            if not original:
                raise ValueError(f"row {number}: publication not found in source corpus")
            abstract = original.get("abstract_text") or ""
            if not isinstance(abstract, str) or normalize_quote(quote) not in normalize_quote(abstract):
                raise ValueError(f"row {number}: evidence quote absent from source abstract")
            if title != original.get("title") or row.get("source_url") != original.get("source_url"):
                raise ValueError(f"row {number}: publication title or URL differs from source")
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
    parser.add_argument("--source-corpus", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(convert(args.input, args.output, args.source_corpus), sort_keys=True))
