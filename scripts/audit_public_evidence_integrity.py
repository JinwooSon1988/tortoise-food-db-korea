#!/usr/bin/env python3
"""Read-only public evidence reference audit. No data mutation or publishing."""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
def load(name):
    return json.loads((ROOT / "data" / name).read_text(encoding="utf-8"))

def audit():
    plants = load("plants.json")
    evidence_doc = load("public_evidence_records.json")
    evidence = evidence_doc["records"] if isinstance(evidence_doc, dict) else evidence_doc
    assessments = load("public_assessments.json")
    problems = []
    def duplicate(rows, field, group):
        counts = Counter(str(x.get(field, "")) for x in rows)
        for value, count in counts.items():
            if not value or count > 1:
                problems.append(f"{group}: invalid/duplicate {field}={value!r} count={count}")
    duplicate(plants, "id", "plants")
    duplicate(evidence, "id", "evidence")
    plant_ids = {x.get("id") for x in plants}
    evidence_ids = {x.get("id") for x in evidence}
    for rec in evidence:
        rid = rec.get("id")
        if not rec.get("plant_ids") or not isinstance(rec["plant_ids"], list):
            problems.append(f"evidence {rid}: missing plant_ids")
        for pid in rec.get("plant_ids", []):
            if pid not in plant_ids:
                problems.append(f"evidence {rid}: unknown plant {pid}")
        for field in ("source_title", "source_type", "animal_taxon", "url"):
            if not rec.get(field):
                problems.append(f"evidence {rid}: missing {field}")
        if rec.get("url") and not str(rec["url"]).startswith(("https://", "http://")):
            problems.append(f"evidence {rid}: malformed source URL")
    for a in assessments:
        pid = a.get("plant_id")
        if pid not in plant_ids:
            problems.append(f"assessment: unknown plant {pid}")
        for eid in a.get("evidence_ids", []):
            if eid not in evidence_ids:
                problems.append(f"assessment {pid}: unknown evidence {eid}")
            else:
                record = next(r for r in evidence if r.get("id") == eid)
                if pid not in record.get("plant_ids", []):
                    problems.append(f"assessment {pid}: evidence {eid} does not reference plant")
    print(f"Plants={len(plants)} Evidence={len(evidence)} Assessments={len(assessments)} Issues={len(problems)}")
    for issue in problems[:200]:
        print("ISSUE:", issue)
    if len(problems) > 200:
        print(f"... {len(problems)-200} additional issues")
    return bool(problems)

if __name__ == "__main__":
    raise SystemExit(1 if audit() else 0)
