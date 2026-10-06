#!/usr/bin/env python3
"""Diagnostic report for assessments combining evidence with different applicability scopes.

Mixed scopes are not errors by themselves. They are surfaced for manual review so
reader-facing claims do not accidentally treat composition-only or broad husbandry
sources as equivalent to exact-taxon feeding evidence.
"""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def load(path):
    raw=json.loads((ROOT/path).read_text(encoding="utf-8"))
    return raw.get("records",raw) if isinstance(raw,dict) else raw

assessments=load("data/public_assessments.json")
evidence=load("data/public_evidence_records.json")
em={e.get("id"):e for e in evidence}

for a in assessments:
    linked=[em[i] for i in a.get("evidence_ids",[]) if i in em]
    scopes=sorted({str(e.get("applicability")) for e in linked if e.get("applicability")})
    if len(scopes)<2:
        continue
    if any(s in scopes for s in ("composition_only","exact_taxon","species")):
        print(json.dumps({
            "plant_id":a.get("plant_id"),
            "confidence":a.get("confidence"),
            "verdict":a.get("verdict"),
            "scopes":scopes,
            "evidence_ids":a.get("evidence_ids",[])
        },ensure_ascii=False))
