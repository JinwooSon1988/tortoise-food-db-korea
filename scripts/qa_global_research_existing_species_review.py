#!/usr/bin/env python3
"""Ensure the editorial existing-species review cites actual candidate evidence links."""
import json
import re
from pathlib import Path

root = Path(__file__).resolve().parents[1]
candidates = json.loads((root / "data/research/plant_candidates_v1.json").read_text(encoding="utf-8"))["candidates"]
records = {r["evidence_id"]: r for r in json.loads((root / "data/research/tortoise_plant_evidence_v1.json").read_text(encoding="utf-8"))["records"]}
doc = (root / "docs/GLOBAL_RESEARCH_EXISTING_SPECIES_REVIEW_20261014.md").read_text(encoding="utf-8")
linked = [c for c in candidates if c["database_status"] == "species_already_in_database" and c["evidence_ids"]]
errors = []
for c in linked:
    name = c["accepted_name"]
    lines = [line for line in doc.splitlines() if line.startswith(f"| *{name}* |")]
    if len(lines) != 1:
        errors.append(f"{name}: expected one table row, got {len(lines)}")
        continue
    row = lines[0]
    ids = set(re.findall(r"`([a-z][a-z0-9_]*-\d{2})`", row))
    expected = set(c["evidence_ids"])
    if ids != expected:
        errors.append(f"{name}: document IDs {sorted(ids)} != candidate IDs {sorted(expected)}")
    for eid in expected:
        if eid not in records:
            errors.append(f"{name}: evidence ID {eid} missing")

# Require the audit to preserve source-reported plant parts and tortoise taxa.
section = doc.split("## Source-field audit of the four linked records", 1)
if len(section) != 2:
    errors.append("missing source-field audit section")
else:
    for candidate in linked:
        name = candidate["accepted_name"]
        lines = [line for line in section[1].splitlines() if line.startswith(f"| *{name}* /")]
        if len(lines) != 1:
            errors.append(f"{name}: missing or duplicated source-field audit row")
            continue
        row = lines[0]
        for eid in candidate["evidence_ids"]:
            record = records[eid]
            if f"*{record['tortoise_scientific_name']}*" not in row:
                errors.append(f"{name}: wrong or missing tortoise taxon")
            if record["plant_part"] not in row:
                errors.append(f"{name}: source plant part missing from audit row")
            if record["preparation_state"] not in row:
                errors.append(f"{name}: preparation state missing from audit row")


# Guard known source-part mismatches from being described as compatible.
compatibility = doc.split("## Source-to-page compatibility decisions", 1)
if len(compatibility) != 2:
    errors.append("missing source-to-page compatibility review")
else:
    for plant_id, evidence_id, source_part, required_warning in [
        ("figleaf", "crm059_hermanni_2011-05", "fruit", "Explicit part mismatch"),
        ("opuntiapad", "mason_1999-22", "not stated in table", "Unverified part"),
    ]:
        lines = [line for line in compatibility[1].splitlines() if line.startswith(f"| \`{plant_id}\` |")]
        if len(lines) != 1:
            errors.append(f"{plant_id}: missing or duplicated compatibility row")
            continue
        row = lines[0]
        if evidence_id not in row or source_part not in row or required_warning not in row:
            errors.append(f"{plant_id}: evidence, source part, or warning mismatch")

if errors:
    print("\n".join(errors))
    raise SystemExit(1)
print(f"Existing-species review links verified for {len(linked)} candidates")
