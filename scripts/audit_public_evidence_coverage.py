#!/usr/bin/env python3
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
assessment_paths=[ROOT/"data/assessments.json"]+[ROOT/f"data/assessments_korea_addendum{'' if i==1 else '_'+str(i)}.json" for i in range(1,13)]
used=set()
for p in assessment_paths:
    if not p.exists(): continue
    for row in json.loads(p.read_text(encoding="utf-8")):
        used.update(row.get("evidence_ids",[]))
public=json.loads((ROOT/"data/public_evidence_records.json").read_text(encoding="utf-8"))
published={r["id"] for r in public.get("records",[])}
missing=sorted(used-published)
print(f"assessment evidence IDs: {len(used)}")
print(f"public evidence records: {len(published)}")
print(f"public coverage: {len(used & published)}/{len(used)}")
if missing:
    print("Not yet public (migration backlog):")
    for x in missing: print(" -",x)
# Coverage is intentionally informational during migration. Integrity of published
# records is enforced separately by qa_public_evidence_layer.py.
