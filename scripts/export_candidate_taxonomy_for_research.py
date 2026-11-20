#!/usr/bin/env python3
"""Export GBIF taxonomy candidates for research-only name matching, not feeding verdicts."""
import argparse
import csv
import hashlib
import json
import re
from pathlib import Path

BINOMIAL = re.compile(r"^[A-Z][a-z]+ [a-z][a-z-]+$")


def export(index_path, site_csv, output, report, diverse_path=None):
    paths = [index_path, site_csv, output, report] + ([diverse_path] if diverse_path else [])
    if len({p.resolve() for p in paths}) != len(paths) or output.exists() or report.exists():
        raise ValueError("paths must be distinct and outputs new")
    index = json.loads(index_path.read_text(encoding="utf-8"))
    shards = index.get("shards")
    if not isinstance(shards, list) or not shards:
        raise ValueError("missing taxonomy shards")
    names = set()
    source_count = 0
    for shard in shards:
        filename = shard.get("file")
        if not isinstance(filename, str) or not re.fullmatch("taxa-[0-9]+[.]json", filename):
            raise ValueError("invalid shard filename")
        path = index_path.parent / filename
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != shard.get("sha256"):
            raise ValueError(f"shard checksum mismatch: {filename}")
        data = json.loads(raw)
        records = data.get("records")
        if not isinstance(records, list) or len(records) != shard.get("count"):
            raise ValueError(f"shard count mismatch: {filename}")
        for record in records:
            name = record.get("scientific_name")
            if (record.get("source_scope") != "taxonomy_only"
                    or record.get("identity_status") != "taxonomy_candidate"
                    or record.get("feeding_safety_status") != "not_assessed"
                    or record.get("safety_grade") is not None
                    or not isinstance(record.get("source_taxon_url"), str)
                    or not record["source_taxon_url"].startswith("https://www.gbif.org/species/")):
                raise ValueError(f"unsafe/unverified taxonomy status in {filename}")
            source_count += 1
            if isinstance(name, str) and BINOMIAL.fullmatch(name):
                names.add(name)
    if source_count != index.get("count"):
        raise ValueError("taxonomy index count mismatch")
    diverse_count = 0
    if diverse_path is not None:
        diverse = json.loads(diverse_path.read_text(encoding="utf-8"))
        records = diverse.get("records")
        if (not isinstance(records, list)
                or diverse.get("record_count") != len(records)
                or not records):
            raise ValueError("diverse taxonomy record count mismatch")
        for row_number, record in enumerate(records, 1):
            name = record.get("scientific_name")
            if not isinstance(name, str) or not BINOMIAL.fullmatch(name):
                raise ValueError(f"invalid diverse binomial at row {row_number}")
            if (record.get("source_scope") != "taxonomy_only"
                    or record.get("identity_status") != "taxonomy_candidate"
                    or not isinstance(record.get("source_taxon_url"), str)
                    or not record["source_taxon_url"].startswith("https://www.gbif.org/species/")
                    or record.get("safety_grade") not in (None, "")
                    or record.get("feeding_safety_status") not in (None, "not_assessed")
                    or record.get("feeding_record_status") in ("verified", "confirmed", "feeding_pending")):
                raise ValueError(f"unsafe diverse taxonomy assertion at row {row_number}")
            names.add(name)
            diverse_count += 1
    with site_csv.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or "plant_scientific_name" not in reader.fieldnames:
            raise ValueError("site taxonomy missing plant_scientific_name")
        for row in reader:
            name = (row.get("plant_scientific_name") or "").strip()
            if not BINOMIAL.fullmatch(name):
                raise ValueError("invalid site binomial")
            names.add(name)
    output.parent.mkdir(parents=True, exist_ok=True)
    report.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["plant_scientific_name"])
        writer.writerows((name,) for name in sorted(names))
    summary = {"taxonomy_candidate_records": source_count,
               "diverse_taxonomy_candidate_records": diverse_count,
               "unique_matching_binomials": len(names),
               "scope": "research_only_taxonomy_candidates_not_accepted_or_feeding_evidence",
               "feeding_verdict": None}
    with report.open("x", encoding="utf-8") as stream:
        json.dump(summary, stream, indent=2)
        stream.write("\n")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("index", type=Path)
    parser.add_argument("--site", type=Path, required=True)
    parser.add_argument("--diverse", type=Path, help="Optional reviewed-structure diverse taxonomy candidates")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(export(args.index, args.site, args.output, args.report, args.diverse), sort_keys=True))
