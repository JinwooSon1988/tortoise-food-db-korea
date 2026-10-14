#!/usr/bin/env python3
"""Read-only publication gate for the separate Unit 2 research branch.

Run on a checkout containing data/research/*_v2.json (e.g. Unit 2 branch).
Do not import v2 into public verdict data.
"""
import json
from collections import Counter
from pathlib import Path

root = Path(__file__).resolve().parents[1]
path = root / "data/research/tortoise_plant_evidence_v2.json"
if not path.exists():
    raise SystemExit("Unit 2 evidence JSON missing; run on the Unit 2 research branch")
data = json.loads(path.read_text(encoding="utf-8"))
records = data["records"]
errors = []
if len(records) != 357:
    errors.append(f"Unit 2 evidence count changed: {len(records)}")
ids = [r["evidence_id"] for r in records]
if len(ids) != len(set(ids)):
    errors.append("Duplicate Unit 2 evidence IDs")
counts = Counter(r["evidence_directness"] for r in records)
expected = {"primary_study_read": 323, "local_report_recorded_in_primary_study_read": 12, "statement_of_the_source_read": 16, "reported_in_source_primary_not_read": 6}
if counts != expected:
    errors.append(f"Directness breakdown changed: {dict(counts)}")
for r in records:
    if r.get("feeding_grade") is not None:
        errors.append(f"Research-only grade must be null: {r['evidence_id']}")
    if not r.get("tortoise_scientific_name") or not r.get("plant_name_as_printed"):
        errors.append(f"Taxon or plant name missing: {r['evidence_id']}")
    if r.get("applies_to_other_tortoise_species") not in ("not established by this source", None):
        errors.append(f"Unreviewed cross-species applicability: {r['evidence_id']}")
by_id = {r["evidence_id"]: r for r in records}
for key in ("lagarde_2003_primary-01", "lagarde_2003_primary-02"):
    if key not in by_id:
        errors.append(f"Critical source review missing: {key}")
if "lagarde_2003_primary-01" in by_id:
    r = by_id["lagarde_2003_primary-01"]
    if r.get("plant_accepted_name") is not None or "conflict" not in str(r.get("plant_name_check", "")):
        errors.append("Ceratocephalus taxonomy conflict must remain unresolved")
if "lagarde_2003_primary-02" in by_id:
    r = by_id["lagarde_2003_primary-02"]
    if r.get("plant_part") != "flower" and r.get("plant_part") != "flowers":
        errors.append("Papaver pavoninum flower-specific evidence was lost")
if errors:
    raise SystemExit("\n".join(errors))
print(f"Unit 2 research-only publication gates passed: {len(records)} evidence records, no feeding grades")
