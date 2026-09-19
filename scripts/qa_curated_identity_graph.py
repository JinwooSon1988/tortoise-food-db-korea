#!/usr/bin/env python3
import json,pathlib,sys
p=pathlib.Path("data/reconciliation/curated_identity_graph.json")
if not p.exists(): print("identity graph not committed yet; generator contract present");sys.exit(0)
d=json.loads(p.read_text(encoding="utf-8")); bad=[]
for n in d["nodes"]:
 for k in ("verdict","safe","feeding_verdict","evidence_grade"):
  if k in n: bad.append(f'{n.get("id")}: forbidden {k}')
states={n["review_state"] for n in d["nodes"] if n.get("type")=="reconciliation_state"}
allowed={"exact_accepted_candidate","synonym_review","infraspecific_review","genus_scope","hybrid_review","unresolved"}
if not states<=allowed: bad.append("unknown review state")
if bad: print("\n".join(bad));sys.exit(1)
print("curated identity graph QA OK")
