#!/usr/bin/env python3
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
records=json.loads((ROOT/"data/public_evidence_records.json").read_text(encoding="utf-8")).get("records",[])
ev={r["id"]:r for r in records}
paths=[ROOT/"data/assessments.json"]+sorted((ROOT/"data").glob("assessments_korea_addendum*.json"))
group=re.compile(r"(?:Mediterranean\s+Testudo|지중해\s*Testudo|지중해\s*육지거북)",re.I)
positive=re.compile(r"(?:사육근거|직접근거|직접관찰|직접\s*섭식|근거가|근거를|자료가|자료를|지지)",re.I)
negative=re.compile(r"(?:없|아님|아니|미확립|확립되지|확인되지|확대하지|의미하지|확정하지)",re.I)
errors=[];checked=0
for path in paths:
    if not path.exists(): continue
    for row in json.loads(path.read_text(encoding="utf-8")):
        checked+=1
        claims=[]
        for field in (str(row.get("why","")),str(row.get("applicability_note",""))):
            for sentence in re.split(r"(?<=[.!?])\s+|\n+",field):
                if group.search(sentence) and positive.search(sentence) and not negative.search(sentence):
                    claims.append(sentence)
        if not claims: continue
        linked=[ev[e] for e in row.get("evidence_ids",[]) if e in ev]
        supported=any(x.get("applicability") in {"mediterranean_testudo","exact_taxon"} and x.get("directness") in {"direct","contextual"} for x in linked)
        if not supported:
            errors.append(f"{path.name}:{row.get('plant_id')}: Mediterranean Testudo claim lacks linked group/exact evidence")
if errors: raise SystemExit("Mediterranean claim guard failed:\n- "+"\n- ".join(errors))
print(f"Mediterranean claim guard passed: {checked} assessments checked.")
