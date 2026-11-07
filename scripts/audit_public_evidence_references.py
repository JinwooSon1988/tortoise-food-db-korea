#!/usr/bin/env python3
"""Read-only, bulk cross-reference audit of public tortoise food evidence.

Checks identity, source links and assessment->evidence->plant relationships.
Legacy assessments without assessment_scope are reported, not silently changed.
No safety verdicts are inferred. Exit 1 on broken references.
"""
import argparse
import json
from collections import Counter
from pathlib import Path

def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def audit(plants, evidence, assessments):
    issues = []
    warnings = []
    def unique(rows, key, label):
        seen = set()
        for row in rows:
            value = row.get(key)
            if not isinstance(value, str) or not value:
                issues.append(f"{label}: missing {key}")
            elif value in seen:
                issues.append(f"{label}: duplicate {key}={value}")
            seen.add(value)
        return seen
    plant_ids = unique(plants, "id", "plant")
    evidence_ids = unique(evidence, "id", "evidence")
    evidence_by_id = {r["id"]: r for r in evidence if r.get("id")}
    scope_counts = Counter()
    for row in evidence:
        eid = row.get("id", "(missing)")
        for pid in row.get("plant_ids") or []:
            if pid not in plant_ids:
                issues.append(f"evidence {eid}: unknown plant {pid}")
        for key in ("url", "animal_taxon", "plant_part_state"):
            if not row.get(key):
                issues.append(f"evidence {eid}: missing {key}")
    for row in assessments:
        pid = row.get("plant_id", "(missing)")
        if pid not in plant_ids:
            issues.append(f"assessment: unknown plant {pid}")
        scope_counts[row.get("assessment_scope") or "(legacy_absent)"] += 1
        if not row.get("assessment_scope"):
            warnings.append(f"assessment {pid}: legacy missing assessment_scope")
        refs = row.get("evidence_ids") or []
        if not refs:
            issues.append(f"assessment {pid}: empty evidence_ids")
        for eid in refs:
            evidence_row = evidence_by_id.get(eid)
            if evidence_row is None:
                issues.append(f"assessment {pid}: unknown evidence {eid}")
            elif pid not in (evidence_row.get("plant_ids") or []):
                issues.append(f"assessment {pid}: evidence {eid} does not cover this plant")
    return {"counts": {"plants": len(plants), "evidence": len(evidence), "assessments": len(assessments),
                       "assessment_evidence_links": sum(len(r.get("evidence_ids") or []) for r in assessments),
                       "scope_distribution": dict(sorted(scope_counts.items()))},
            "status": "fail" if issues else "pass",
            "errors": issues, "warnings": {"missing_assessment_scope": len(warnings), "examples": warnings[:10]}}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--plants", default="data/plants.json")
    p.add_argument("--evidence", default="data/public_evidence_records.json")
    p.add_argument("--assessments", default="data/public_assessments.json")
    args = p.parse_args()
    raw_evidence = load(args.evidence)
    result = audit(load(args.plants), raw_evidence["records"], load(args.assessments))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["status"] != "pass":
        raise SystemExit(1)

if __name__ == "__main__":
    main()
