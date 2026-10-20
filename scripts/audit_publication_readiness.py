#!/usr/bin/env python3
"""Produce publication readiness audit; taxonomy-only GBIF candidates never auto-publish."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def audit(plants, assessments, records, candidates):
    ids = {p["id"] for p in plants}
    by_evidence = {e["id"]: e for e in records}
    by_assessment = {}
    for a in assessments:
        by_assessment.setdefault(a["plant_id"], []).append(a)
    publishable = []
    issues = []
    for p in plants:
        ass = by_assessment.get(p["id"], [])
        if not ass:
            issues.append({"plant_id": p["id"], "reason": "missing_assessment"})
            continue
        for a in ass:
            links = a.get("evidence_ids") or []
            valid = [by_evidence[k] for k in links if k in by_evidence]
            missing = [k for k in links if k not in by_evidence]
            if missing or not valid or not a.get("verdict"):
                issues.append({"plant_id": p["id"], "reason": "missing_or_broken_evidence", "missing": missing})
                continue
            publishable.append({"plant_id": p["id"], "animal_taxon": a.get("animal_taxon"),
                "verdict": a["verdict"], "evidence_count": len(valid),
                "direct_evidence_count": sum(e.get("directness") == "direct" for e in valid),
                "source_types": sorted({e.get("source_type", "unknown") for e in valid}),
                "has_taxon_scope": bool(a.get("animal_taxon")),
                "has_limitations": bool(a.get("limits"))})
    unassessed = []
    for row in candidates:
        if row.get("feeding_verdict") is not None:
            issues.append({"candidate_id": row.get("candidate_id"), "reason": "unsafe_taxonomy_verdict"})
        else:
            unassessed.append(row.get("candidate_id"))
    return {"summary": {"existing_plants": len(ids), "assessment_rows": len(assessments),
        "evidence_records": len(records), "assessment_rows_with_linked_evidence": len(publishable),
        "taxonomy_only_candidates": len(unassessed), "issues": len(issues)},
        "existing_reviewed": publishable, "taxonomy_only_queue": unassessed, "issues": issues}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--taxonomy-batch", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    plants = json.loads((ROOT / "data/plants.json").read_text(encoding="utf-8"))
    assessments = json.loads((ROOT / "data/public_assessments.json").read_text(encoding="utf-8"))
    records = json.loads((ROOT / "data/public_evidence_records.json").read_text(encoding="utf-8"))["records"]
    candidates = []
    if args.taxonomy_batch:
        payload = json.loads(args.taxonomy_batch.read_text(encoding="utf-8"))
        candidates = payload["candidates"]
    result = audit(plants, assessments, records, candidates)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], ensure_ascii=False))
if __name__ == "__main__":
    main()
