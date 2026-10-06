#!/usr/bin/env python3
"""Report public evidence records that are no longer referenced by any public assessment.

This is diagnostic only. Historical/superseded records are not deleted automatically.
"""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def load(path):
    raw=json.loads((ROOT/path).read_text(encoding="utf-8"))
    return raw.get("records", raw) if isinstance(raw,dict) else raw

evidence=load("data/public_evidence_records.json")
assessments=load("data/public_assessments.json")
used={eid for a in assessments for eid in (a.get("evidence_ids") or [])}
orphans=[{
    "id":e.get("id"),
    "plant_ids":e.get("plant_ids") or [],
    "source_title":e.get("source_title"),
    "locator":e.get("doi") or e.get("pmid") or e.get("url"),
} for e in evidence if e.get("id") not in used]

print(f"Evidence records not referenced by public assessments: {len(orphans)}")
for row in orphans:
    print(json.dumps(row, ensure_ascii=False))
