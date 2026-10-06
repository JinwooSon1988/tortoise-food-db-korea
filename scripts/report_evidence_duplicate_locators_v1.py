#!/usr/bin/env python3
"""Diagnostic audit for duplicated public evidence locators.

Flags repeated DOI/PMID/URL records attached to the same plant. It does not
merge or delete records because separate records may intentionally preserve
different claims from the same source.
"""
import json
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
raw=json.loads((ROOT/"data/public_evidence_records.json").read_text(encoding="utf-8"))
rows=raw.get("records",raw) if isinstance(raw,dict) else raw
groups=defaultdict(list)
for r in rows:
    locator=r.get("doi") or r.get("pmid") or r.get("url")
    if not locator:
        continue
    for pid in r.get("plant_ids") or []:
        groups[(pid,locator)].append(r.get("id"))
hits=[{"plant_id":pid,"locator":loc,"evidence_ids":ids}
      for (pid,loc),ids in groups.items() if len(ids)>1]
print(f"Repeated source locators within the same plant: {len(hits)}")
for h in hits:
    print(json.dumps(h,ensure_ascii=False))
