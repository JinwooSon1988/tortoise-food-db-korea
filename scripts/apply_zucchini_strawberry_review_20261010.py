#!/usr/bin/env python3
"""One-off, re-runnable application of the 2026-10-10 zucchini / strawberry-leaf feeding review.

Sources were re-read on 2026-10-10 (The Tortoise Table plant=627 Squash, plant=637 Courgette, plant=293 Strawberry).
The decision record is data/zucchini_strawberry_feeding_review_20261010.json; this script writes exactly those
changes into data/public_assessments.json and data/public_evidence_records.json (idempotent).
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEW = json.loads((ROOT / "data/zucchini_strawberry_feeding_review_20261010.json").read_text(encoding="utf-8"))
A_PATH = ROOT / "data/public_assessments.json"
E_PATH = ROOT / "data/public_evidence_records.json"

assess = json.loads(A_PATH.read_text(encoding="utf-8"))
evid = json.loads(E_PATH.read_text(encoding="utf-8"))
for item in REVIEW["decisions"]:
    rows = [a for a in assess if a["plant_id"] == item["plant_id"] and a["species_group"] == item["species_group"]]
    assert len(rows) == 1, item["plant_id"]
    rows[0].update(item["after"])
for upd in REVIEW["evidence_updates"]:
    rec = next(r for r in evid["records"] if r["id"] == upd["id"])
    rec.update(upd["after"])
A_PATH.write_text(json.dumps(assess, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
E_PATH.write_text(json.dumps(evid, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("applied:", [d["plant_id"] for d in REVIEW["decisions"]], [u["id"] for u in REVIEW["evidence_updates"]])
