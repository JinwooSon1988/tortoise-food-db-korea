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
if errors:
    print("\n".join(errors))
    raise SystemExit(1)
print(f"Existing-species review links verified for {len(linked)} candidates")
