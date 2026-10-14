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
# Prevent secondary citations from being mislabeled as verified original studies.
unread = [r for r in records if r["evidence_directness"] == "reported_in_source_primary_not_read"]
if len(unread) != 6:
    errors.append(f"Unexpected unread-primary count: {len(unread)}")
for r in unread:
    if r.get("verification_status") != "secondary_source_checked_primary_unread":
        errors.append(f"Unread primary mislabeled as verified: {r['evidence_id']}")
    if r.get("evidence_type") != "secondary_citation_of_species_diet":
        errors.append(f"Unread primary mislabeled as direct evidence type: {r['evidence_id']}")
    if r.get("plant_accepted_name") is not None and r.get("plant_name_check") == "spelling_differs_from_backbone_needs_review":
        errors.append(f"Unresolved secondary name prematurely accepted: {r['evidence_id']}")
moll_secondary = next((r for r in records if r["evidence_id"] == "moll_klemens_1996-07"), None)
if moll_secondary is None:
    errors.append("Missing Moll and Klemens secondary citation")
elif "Secondary citation" not in moll_secondary.get("study_method", "") or "Loveridge and Williams (1957)" not in moll_secondary.get("study_method", ""):
    errors.append("Moll and Klemens secondary citation inherited direct observation method")
for key in ("delaossa_2009-20", "delaossa_2009-21", "delaossa_2009-22", "delaossa_2009-23", "delaossa_2009-24"):
    r = next((x for x in records if x["evidence_id"] == key), None)
    if r is None:
        errors.append(f"Missing De la Ossa secondary citation: {key}")
    elif "Secondary background citation" not in r.get("study_method", ""):
        errors.append(f"De la Ossa secondary citation inherited captive trial method: {key}")
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
