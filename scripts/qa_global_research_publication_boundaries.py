#!/usr/bin/env python3
"""Block unsafe publication assumptions in the global tortoise diet research layer."""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1] / "data/research"
candidates = json.loads((root / "plant_candidates_v1.json").read_text(encoding="utf-8"))["candidates"]
records = json.loads((root / "tortoise_plant_evidence_v1.json").read_text(encoding="utf-8"))["records"]
by_id = {r["evidence_id"]: r for r in records}
errors = []

for r in records:
    if r.get("feeding_grade") is not None:
        errors.append(f"{r['evidence_id']}: research observation assigned feeding grade")
    if r.get("is_negative_record") and r.get("observed_consumption") not in ("avoided", "usually avoided", "generally rejected"):
        errors.append(f"{r['evidence_id']}: negative record with unrecognized observation")

for c in candidates:
    if c.get("feeding_grade") is not None:
        errors.append(f"{c['candidate_key']}: research candidate assigned feeding grade")
    linked = [by_id[i] for i in c["evidence_ids"] if i in by_id]
    if c.get("negative_record_only") and (not linked or any(not r.get("is_negative_record") for r in linked)):
        errors.append(f"{c['candidate_key']}: negative-only label conflicts with evidence")
    if linked and all(r.get("is_negative_record") for r in linked) and not c.get("negative_record_only"):
        errors.append(f"{c['candidate_key']}: exclusively negative evidence not marked negative-only")

if errors:
    print("Research publication boundary QA failed:")
    print("\n".join(errors))
    raise SystemExit(1)
print(f"Publication boundary QA passed: {len(candidates)} candidates, {len(records)} records")
