#!/usr/bin/env python3
import json, pathlib, sys
P=pathlib.Path(__file__).resolve().parents[1]
files=list((P/"data/staging").glob("global_plant_candidates*.json")) if (P/"data/staging").exists() else []
errors=[]
for f in files:
    rows=json.loads(f.read_text(encoding="utf-8")); ids=set()
    for i,r in enumerate(rows):
        cid=r.get("candidate_id")
        if not cid or cid in ids: errors.append(f"{f}:{i}: duplicate/missing candidate_id")
        ids.add(cid)
        for k in ("canonical_scientific_name","source_id","source_url","observed_at","reconciliation_status"):
            if not r.get(k): errors.append(f"{f}:{cid}: {k} required")
        if r.get("feed_review_status")!="identity_only": errors.append(f"{f}:{cid}: staging candidates must remain identity_only")
        forbidden={"verdict","safe","feeding_verdict","feed_assessment"}
        if forbidden.intersection(r): errors.append(f"{f}:{cid}: feeding judgement forbidden in raw staging")
if errors:
    print("\n".join(errors)); sys.exit(1)
print(f"global plant staging QA OK: {len(files)} files")
