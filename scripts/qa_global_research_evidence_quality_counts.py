#!/usr/bin/env python3
"""Verify the dated evidence-quality audit baseline against research records.

A future expansion that changes these counts intentionally fails until the
editorial review and baseline are updated together; it does not block research
collection itself, only this review gate.
"""
import json
import re
from collections import Counter
from pathlib import Path

root = Path(__file__).resolve().parents[1]
records = json.loads((root / "data/research/tortoise_plant_evidence_v1.json").read_text(encoding="utf-8"))["records"]
doc = (root / "docs/GLOBAL_RESEARCH_EVIDENCE_QUALITY_BOTTLENECKS_20261014.md").read_text(encoding="utf-8")
expected = {
    "primary_study_read": 46,
    "reported_in_account_primary_not_read": 102,
    "statement_of_the_source_read": 21,
}
actual = Counter(r.get("evidence_directness") for r in records)
errors = []
if actual != expected:
    errors.append(f"evidence directness counts changed: {dict(actual)} != {expected}")
if len(records) != 169:
    errors.append(f"record count changed: {len(records)} != 169")
unknown_parts = sum(bool(re.search(r"not stated|unknown|unspecified", r.get("plant_part", ""), re.I)) for r in records)
if unknown_parts != 104:
    errors.append(f"unclear plant parts changed: {unknown_parts} != 104")
negative = sum(r.get("is_negative_record") is True for r in records)
if negative != 7:
    errors.append(f"negative observation count changed: {negative} != 7")
for text in ["**104**", "**7**", "**No automatic grade or safety approval**", "102 records"]:
    if text not in doc:
        errors.append(f"document warning/count missing: {text}")
if errors:
    raise SystemExit("\n".join(errors))
print("Evidence-quality audit passed: 169 records; 102 indirect; 104 unclear parts; 7 negative")
