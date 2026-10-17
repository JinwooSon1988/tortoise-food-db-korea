#!/usr/bin/env python3
"""Audit evidence-to-plant linkage and TTT provenance without inferring safety."""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
plants = json.loads((ROOT / "data/plants.json").read_text(encoding="utf-8"))
assessments = json.loads((ROOT / "data/public_assessments.json").read_text(encoding="utf-8"))
records = json.loads((ROOT / "data/public_evidence_records.json").read_text(encoding="utf-8"))["records"]
plant_ids = {p["id"] for p in plants}
evidence = {r["id"]: r for r in records}
issues = []
links = []
for a in assessments:
    pid = a["plant_id"]
    for eid in a.get("evidence_ids", []):
        rec = evidence.get(eid)
        if not rec:
            issues.append({"plant_id": pid, "evidence_id": eid, "issue": "missing_evidence"})
            continue
        if pid not in rec.get("plant_ids", []):
            issues.append({"plant_id": pid, "evidence_id": eid, "issue": "evidence_plant_scope_mismatch"})
        links.append({"plant_id": pid, "evidence_id": eid,
                      "source_type": rec.get("source_type"),
                      "directness": rec.get("directness"),
                      "source_url": rec.get("url"),
                      "animal_taxon": rec.get("animal_taxon"),
                      "plant_taxon": rec.get("plant_taxon"),
                      "plant_part": rec.get("plant_part_state"),
                      "ttt_source": "thetortoisetable.org.uk" in (rec.get("url") or "").lower(),
                      "independently_verified_in_this_audit": False})
for r in records:
    for pid in r.get("plant_ids", []):
        if pid not in plant_ids:
            issues.append({"plant_id": pid, "evidence_id": r["id"], "issue": "unknown_plant"})
ttt = [r for r in records if "thetortoisetable.org.uk" in (r.get("url") or "").lower()]
result = {"summary": {"plants": len(plants), "assessments": len(assessments),
    "evidence_records": len(records), "linked_assessment_evidence_pairs": len(links),
    "ttt_source_records": len(ttt), "structural_issues": len(issues),
    "warning": "Linked evidence is not equivalent to independent scientific verification."},
    "source_type_counts": dict(Counter(r.get("source_type", "unknown") for r in records)),
    "ttt_evidence_ids": [r["id"] for r in ttt],
    "linked_records": links, "issues": issues}
out = ROOT / "research/generated/evidence_linkage_provenance_audit.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result["summary"], ensure_ascii=False))
if issues:
    raise SystemExit(f"Evidence structural integrity failed: {len(issues)} issues")
