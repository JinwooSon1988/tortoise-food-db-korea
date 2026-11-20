#!/usr/bin/env python3
"""Produce a research-only coverage report for the entire botanical name index."""
import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


def coverage(taxonomy, abstracts, fulltexts, output, report):
    paths = [taxonomy, abstracts, output, report] + ([fulltexts] if fulltexts else [])
    if len({p.resolve() for p in paths}) != len(paths) or output.exists() or report.exists():
        raise ValueError("all paths must be distinct and outputs new")
    with taxonomy.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or "plant_scientific_name" not in reader.fieldnames:
            raise ValueError("taxonomy requires plant_scientific_name")
        names = [row["plant_scientific_name"] for row in reader]
    if not names or any(not name for name in names) or len(names) != len(set(names)):
        raise ValueError("taxonomy must contain unique nonempty names")
    known = set(names)
    sources = defaultdict(lambda: {"abstract": set(), "fulltext": set()})
    for scope, path in (("abstract", abstracts), ("fulltext", fulltexts)):
        if path is None:
            continue
        with path.open(encoding="utf-8") as stream:
            for number, line in enumerate(stream, 1):
                if not line.strip():
                    continue
                record = json.loads(line)
                name = record.get("plant_scientific_name")
                if name not in known or record.get("source_scope") != scope:
                    raise ValueError(f"invalid {scope} link at line {number}")
                if record.get("feeding_verdict") is not None or record.get("review_status") != f"unverified_{scope}_mention":
                    raise ValueError(f"unsafe review state at {scope} line {number}")
                identity = (record.get("source_database"), str(record.get("source_record_id") or ""))
                if not all(identity):
                    raise ValueError(f"missing publication identity at {scope} line {number}")
                sources[name][scope].add(identity)
    output.parent.mkdir(parents=True, exist_ok=True)
    report.parent.mkdir(parents=True, exist_ok=True)
    counts = Counter()
    with output.open("x", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["plant_scientific_name", "abstract_publications", "fulltext_publications",
                         "research_mention_status", "feeding_verdict"])
        for name in sorted(known):
            a, f = len(sources[name]["abstract"]), len(sources[name]["fulltext"])
            status = "unverified_mention" if a or f else "no_exact_mention_found"
            writer.writerow([name, a, f, status, ""])
            counts[status] += 1
    summary = {"taxonomy_species": len(known), "species_with_unverified_mentions":
               counts["unverified_mention"], "species_without_exact_mentions":
               counts["no_exact_mention_found"], "feeding_verdict": None,
               "caveat": "A missing exact mention does not prove absence of evidence; mentions do not establish feeding safety."}
    with report.open("x", encoding="utf-8") as stream:
        json.dump(summary, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--taxonomy", required=True, type=Path)
    parser.add_argument("--abstracts", required=True, type=Path)
    parser.add_argument("--fulltexts", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(coverage(args.taxonomy, args.abstracts, args.fulltexts,
                              args.output, args.report), sort_keys=True))
