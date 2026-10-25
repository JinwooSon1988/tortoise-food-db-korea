#!/usr/bin/env python3
"""Read-only evidence coverage and publication-safety report; no verdict promotion."""
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
def read(name):
    return json.loads((ROOT / "data" / name).read_text(encoding="utf-8"))

def main():
    evidence = read("public_evidence_records.json")["records"]
    assessments = read("public_assessments.json")
    plants = read("plants.json")
    counts = Counter()
    plants_by_evidence = defaultdict(set)
    for record in evidence:
        counts["evidence_records"] += 1
        for pid in record.get("plant_ids", []):
            plants_by_evidence[pid].add(record["id"])
        if not record.get("animal_taxon") or not record.get("plant_part_state"):
            counts["incomplete_scope_or_part"] += 1
        if not record.get("supports") or not record.get("does_not_support"):
            counts["missing_support_or_limits"] += 1
        if not str(record.get("url", "")).startswith(("https://", "http://")):
            counts["missing_source_url"] += 1
        if record.get("source_type") in ("peer_reviewed_human_nutrition", "peer_reviewed_food_chemistry", "authoritative_taxonomy_database", "taxonomy_database", "taxonomic_database"):
            counts["context_only_source_type"] += 1
    counts["catalog_plants"] = len(plants)
    counts["assessments"] = len(assessments)
    counts["plants_with_evidence"] = len(plants_by_evidence)
    counts["plants_without_evidence"] = sum(p["id"] not in plants_by_evidence for p in plants)
    counts["assessment_without_evidence_ids"] = sum(not a.get("evidence_ids") for a in assessments)
    report = {"summary": dict(sorted(counts.items())), "note": "Evidence linkage does not establish feeding safety; context-only records require independent feeding evidence."}
    print(json.dumps(report, ensure_ascii=False, indent=2))
if __name__ == "__main__":
    main()
