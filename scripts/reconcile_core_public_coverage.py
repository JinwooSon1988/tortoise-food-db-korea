#!/usr/bin/env python3
"""Read-only cross-dataset coverage reconciliation; never modifies verdicts."""
import json
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
def load(path):
    return json.loads(path.read_text(encoding="utf-8"))
def main():
    plants = load(DATA / "plants.json")
    records = load(DATA / "public_evidence_records.json")["records"]
    assessments = load(DATA / "public_assessments.json")
    linked = set()
    types = Counter()
    for record in records:
        linked.update(record.get("plant_ids", []))
        types[record.get("source_type", "unknown")] += 1
    core_ids = {p["id"] for p in plants}
    report = {
        "core_plants": len(core_ids),
        "core_plants_with_any_record": len(core_ids & linked),
        "core_plants_without_any_record": sorted(core_ids - linked),
        "public_evidence_records": len(records),
        "public_assessments": len(assessments),
        "assessments_missing_evidence_ids": sorted({a.get("plant_id") for a in assessments if not a.get("evidence_ids")}),
        "source_type_counts": dict(sorted(types.items())),
        "warning": "A linked record is not proof of feeding or safety. This audit does not measure the global 22,765 taxon corpus."
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
if __name__ == "__main__":
    main()
