#!/usr/bin/env python3
"""Batch link exact plant binomials to Europe PMC abstracts for manual review only."""
import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path

BINOMIAL = re.compile(r"^[A-Z][a-z]+ [a-z][a-z-]+$")
MAX_TERMS = 100000
# Fixed-size candidate recognizer: taxonomy size does not inflate the regex.
CANDIDATE_BINOMIAL = re.compile(r"(?<![A-Za-z])([A-Z][a-z]+ [a-z][a-z-]+)(?![A-Za-z])")


def load_taxa(path):
    taxa = set()
    with path.open(encoding="utf-8-sig", newline="") as stream:
        for number, row in enumerate(csv.DictReader(stream), 2):
            name = (row.get("plant_scientific_name") or "").strip()
            if not BINOMIAL.fullmatch(name):
                raise ValueError(f"invalid binomial in taxonomy row {number}")
            taxa.add(name)
            if len(taxa) > MAX_TERMS:
                raise ValueError("taxonomy limit exceeded")
    if not taxa:
        raise ValueError("empty taxonomy")
    return taxa


def link(abstract_path, taxonomy_path, output_path, report_path, source_scope="abstract"):
    if source_scope not in ("abstract", "fulltext"):
        raise ValueError("source_scope must be abstract or fulltext")
    paths = [abstract_path, taxonomy_path, output_path, report_path]
    if len({x.resolve() for x in paths}) != 4 or output_path.exists() or report_path.exists():
        raise ValueError("paths must be distinct and outputs new")
    taxa = load_taxa(taxonomy_path)
    # Scan each document once and resolve candidates against the accepted-name set.
    # This avoids compiling a potentially 100,000-term alternation.
    results = []
    counts = Counter()
    seen = set()
    with abstract_path.open(encoding="utf-8") as stream:
        for number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("review_status") != "unmatched_literature_lead" or record.get("feeding_verdict") is not None:
                raise ValueError(f"invalid literature record at line {number}")
            identity = (record.get("source_database"), str(record.get("source_record_id") or ""))
            if not all(identity) or identity in seen:
                raise ValueError(f"duplicate/missing publication identity at line {number}")
            seen.add(identity)
            abstract = record.get("abstract_text") or ""
            if not isinstance(abstract, str):
                raise ValueError(f"invalid abstract at line {number}")
            normalized = re.sub(r"<[^>]*>", " ", abstract)
            matches = {}
            for match in CANDIDATE_BINOMIAL.finditer(normalized):
                plant = match.group(1)
                if plant not in taxa:
                    continue
                if plant not in matches:
                    left = max(0, match.start() - 180)
                    right = min(len(normalized), match.end() + 180)
                    matches[plant] = " ".join(normalized[left:right].split())
            mentions = sorted(matches)
            counts["publications_screened"] += 1
            if mentions:
                counts["publications_with_exact_plant_mentions"] += 1
            for plant in mentions:
                results.append({
                    "plant_scientific_name": plant,
                    "source_database": identity[0], "source_record_id": identity[1],
                    "source_title": record.get("title"), "source_url": record.get("source_url"),
                    "doi": record.get("doi"), "review_status": "unverified_" + source_scope + "_mention",
                    "source_scope": source_scope, "mention_context": matches[plant],
                    "tortoise_scientific_name": None, "plant_part": None,
                    "feeding_verdict": None,
                    "note": "Exact taxon mention in " + source_scope + " only; NOT evidence of consumption or safety."})
                counts["unverified_plant_publication_links"] += 1
    if not seen:
        raise ValueError("empty literature corpus")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("x", encoding="utf-8") as stream:
        for item in results:
            stream.write(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n")
    with report_path.open("x", encoding="utf-8") as stream:
        json.dump({"counts": dict(counts), "taxonomy_species": len(taxa),
                   "status": "unverified_" + source_scope + "_mentions_only"}, stream, indent=2)
        stream.write("\n")
    return dict(counts)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("literature", type=Path)
    parser.add_argument("--taxonomy", required=True, type=Path,
                        help="CSV with plant_scientific_name column; accepted identities only")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--source-scope", choices=("abstract", "fulltext"), default="abstract")
    args = parser.parse_args()
    print(json.dumps(link(args.literature, args.taxonomy, args.output, args.report, args.source_scope), sort_keys=True))
