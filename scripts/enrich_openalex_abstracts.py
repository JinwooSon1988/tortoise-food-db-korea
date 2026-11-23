#!/usr/bin/env python3
"""Bulk OpenAlex abstract retrieval for existing leads; never infer feeding safety."""
import argparse
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

OPENALEX_ID = re.compile(r"^https://openalex\.org/(W[0-9]+)$")


def decode_abstract(index):
    if not isinstance(index, dict):
        return None
    positions = []
    for word, offsets in index.items():
        if not isinstance(word, str) or not isinstance(offsets, list):
            raise ValueError("malformed abstract index")
        for position in offsets:
            if not isinstance(position, int) or position < 0:
                raise ValueError("invalid abstract position")
            positions.append((position, word))
    if len({p for p, _ in positions}) != len(positions):
        raise ValueError("duplicate abstract position")
    return " ".join(word for _, word in sorted(positions))


def chunks(values, size=25):
    if not 1 <= size <= 50:
        raise ValueError("batch size outside supported bound")
    for i in range(0, len(values), size):
        yield values[i:i + size]


def enrich(works, fetch, sleep=time.sleep, batch_size=25, interval=3):
    if interval < 1:
        raise ValueError("interval must be >=1")
    ids = sorted({m.group(1) for w in works if isinstance(w.get("openalex_id"), str)
                  if (m := OPENALEX_ID.fullmatch(w["openalex_id"]))})
    results = {}
    for number, group in enumerate(chunks(ids, batch_size)):
        if number:
            sleep(interval)
        url = "https://api.openalex.org/works?" + urllib.parse.urlencode({
            "filter": "openalex_id:" + "|".join(group),
            "per-page": str(len(group)),
            "select": "id,doi,title,abstract_inverted_index,publication_year",
        })
        response = fetch(url)
        if not isinstance(response.get("results"), list):
            raise ValueError("invalid OpenAlex results")
        for work in response["results"]:
            match = OPENALEX_ID.fullmatch(work.get("id") or "")
            if match and match.group(1) in group:
                results[match.group(1)] = {
                    "openalex_id": work["id"],
                    "abstract": decode_abstract(work.get("abstract_inverted_index")),
                    "status": "abstract_unreviewed",
                    "feeding_confirmed": False,
                }
    return {"scope": "research_only_unreviewed_abstracts",
            "input_unique_ids": len(ids), "abstracts_returned": len(results),
            "abstracts_available": sum(bool(r["abstract"]) for r in results.values()),
            "feeding_verdicts_confirmed": 0,
            "records": sorted(results.values(), key=lambda x: x["openalex_id"])}


def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "GeobukbapResearch/0.1",
                                               "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("input", type=Path)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--batch-size", type=int, default=25)
    args = p.parse_args()
    if args.input.resolve() == args.output.resolve():
        p.error("input and output must differ")
    data = json.loads(args.input.read_text(encoding="utf-8"))
    if data.get("scope") != "literature_first_unreviewed_not_feeding_evidence":
        p.error("unsupported input evidence scope")
    report = enrich(data["works"], fetch_json, batch_size=args.batch_size)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("input_unique_ids", "abstracts_available", "feeding_verdicts_confirmed")}))


if __name__ == "__main__":
    main()
