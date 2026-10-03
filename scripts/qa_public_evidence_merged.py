from pathlib import Path
import json,re,sys
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"
def order(p):
    m=re.search(r"_(\d+)\.json$",p.name)
    return int(m.group(1)) if m else 0

paths=[DATA/"evidence_records.json"]+sorted(DATA.glob("evidence_records_addendum*.json"),key=order)
merged={}
for p in paths:
    if not p.exists():
        continue
    data=json.loads(p.read_text(encoding="utf-8"))
    rows=data.get("records",[]) if isinstance(data,dict) else data
    if not isinstance(rows,list):
        continue
    for row in rows:
        rid=row.get("id")
        if rid:
            merged[rid]=row

actual_doc=json.loads((DATA/"public_evidence_records.json").read_text(encoding="utf-8"))
actual=actual_doc.get("records",[])
actual_by={x.get("id"):x for x in actual if x.get("id")}
errors=[]
if merged != actual_by:
    missing=sorted(set(merged)-set(actual_by))
    extra=sorted(set(actual_by)-set(merged))
    changed=sorted(k for k in set(merged)&set(actual_by) if merged[k]!=actual_by[k])
    errors.append(f"public evidence drift: source={len(merged)} public={len(actual_by)} missing={missing[:10]} extra={extra[:10]} changed={changed[:10]}")

assess=json.loads((DATA/"public_assessments.json").read_text(encoding="utf-8"))
for row in assess:
    for eid in row.get("evidence_ids",[]):
        if eid not in actual_by:
            errors.append(f"{row.get('plant_id')}/{row.get('species_group')}: missing public evidence_id {eid}")

if errors:
    print("FAIL")
    for e in errors: print("-",e)
    sys.exit(1)
print(f"PASS public evidence: {len(actual_by)} records; all public assessment evidence_ids resolve")
