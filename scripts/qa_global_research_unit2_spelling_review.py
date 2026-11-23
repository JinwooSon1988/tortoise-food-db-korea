#!/usr/bin/env python3
"""Guard Unit 2 editorial spelling hypotheses against accidental source rewriting."""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
records = json.loads((root / "data/research/tortoise_plant_evidence_v2.json").read_text(encoding="utf-8"))["records"]
rows = [r for r in records if r["plant_name_check"] == "spelling_differs_from_backbone_needs_review"]
doc = (root / "docs/GLOBAL_RESEARCH_UNIT2_SPELLING_REVIEW_20261014.md").read_text(encoding="utf-8")
errors = []
if len(rows) != 13:
    errors.append(f"Expected 13 spelling-discrepancy records; got {len(rows)}")
for row in rows:
    expected_prefix = f"| \`{row['evidence_id']}\` | {row['plant_name_as_printed']} |"
    expected_prefix = expected_prefix.replace("\\", "")
    if expected_prefix not in doc:
        errors.append(f"Missing exact source name in editorial table: {row['evidence_id']}")
    if row.get("plant_accepted_name") is not None:
        errors.append(f"Unreviewed accepted name assigned: {row['evidence_id']}")
for phrase in ("not confirmed botanical corrections", "not independently verified corrections", "must **not** be written"):
    if phrase not in doc:
        errors.append(f"Missing explicit hypothesis warning: {phrase}")
if errors:
    raise SystemExit("\n".join(errors))
print("Unit 2 spelling review verified: 13 original names preserved, no accepted-name assignments")
