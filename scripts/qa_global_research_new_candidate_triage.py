#!/usr/bin/env python3
"""Verify published editorial candidate counts against the research inventory."""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
data = json.loads((root / "data/research/plant_candidates_v1.json").read_text(encoding="utf-8"))
records = {r["evidence_id"]: r for r in json.loads((root / "data/research/tortoise_plant_evidence_v1.json").read_text(encoding="utf-8"))["records"]}
candidates = [c for c in data["candidates"] if c["database_status"] == "not_in_database"]
doc = (root / "docs/GLOBAL_RESEARCH_NEW_CANDIDATE_TRIAGE_20261014.md").read_text(encoding="utf-8")
groups = {
    ("species", True): 89,
    ("genus", True): 33,
    ("species", False): 6,
    ("genus", False): 1,
}
errors = []
for (rank, linked), expected in groups.items():
    actual = sum(c["rank"] == rank and bool(c["evidence_ids"]) == linked for c in candidates)
    if actual != expected:
        errors.append(f"{rank}, linked={linked}: actual {actual}, documented {expected}")
if len(candidates) != 129:
    errors.append(f"new candidates: {len(candidates)} != 129")
without = sorted(c["accepted_name"] for c in candidates if not c["evidence_ids"])
negative = sorted(c["accepted_name"] for c in candidates if c["negative_record_only"])
for label, names, expected in [("seed-only", without, 7), ("negative-only", negative, 5)]:
    if len(names) != expected:
        errors.append(f"{label}: {len(names)} != {expected}")
    for name in names:
        if f"*{name}*" not in doc:
            errors.append(f"{label} name absent from document: {name}")
for candidate in candidates:
    if not candidate["evidence_ids"] and not candidate["seed_mixture_ids"]:
        errors.append(f"unlinked candidate lacks seed mixture source: {candidate['accepted_name']}")
    if candidate["negative_record_only"]:
        if not candidate["evidence_ids"]:
            errors.append(f"negative-only candidate has no evidence: {candidate['accepted_name']}")
        for evidence_id in candidate["evidence_ids"]:
            record = records.get(evidence_id)
            if record is None or record.get("is_negative_record") is not True:
                errors.append(f"negative-only candidate has non-negative/missing evidence: {candidate['accepted_name']} / {evidence_id}")
for text in ["| **Total not in database** | **129** |", "**Zero automatically approved**"]:
    if text not in doc:
        errors.append(f"required publication warning missing: {text}")
if errors:
    raise SystemExit("\n".join(errors))
print("New-candidate triage verified: 129 candidates, 7 without observation IDs, 5 negative-only")
