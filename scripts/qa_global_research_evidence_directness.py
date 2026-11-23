#!/usr/bin/env python3
"""Guard evidence directness against accidental promotion of secondary records."""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1] / "data/research"
records = json.loads((root / "tortoise_plant_evidence_v1.json").read_text(encoding="utf-8"))["records"]
sources = {s["source_id"]: s for s in json.loads((root / "global_evidence_sources_v1.json").read_text(encoding="utf-8"))["sources"]}
allowed = {
    ("primary_study_read", "verified_primary_source"),
    ("reported_in_account_primary_not_read", "verified_in_peer_reviewed_account"),
    ("statement_of_the_source_read", "verified_in_peer_reviewed_account"),
    ("statement_of_the_source_read", "verified_abstract_only"),
    ("statement_of_the_source_read", "hold_original_not_read"),
}
errors = []
for e in records:
    pair = (e["evidence_directness"], e["verification_status"])
    if pair not in allowed:
        errors.append(f"{e['evidence_id']}: unexpected evidence directness/status: {pair}")
    s = sources.get(e["source_id"])
    if s and e["evidence_directness"] == "primary_study_read":
        if s["access"] != "full_text_read" or s["verification_status"] != "verified_primary_source":
            errors.append(f"{e['evidence_id']}: primary-study claim not supported by source access")
    if e["evidence_directness"] == "reported_in_account_primary_not_read" and e["verification_status"] == "verified_primary_source":
        errors.append(f"{e['evidence_id']}: indirect account citation promoted to primary evidence")
if errors:
    print("Evidence directness QA failed:")
    print("\n".join(errors))
    raise SystemExit(1)
print(f"Evidence directness QA passed for {len(records)} records")
