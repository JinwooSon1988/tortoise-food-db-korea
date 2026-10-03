from pathlib import Path
import json,re,sys
ROOT=Path(__file__).resolve().parents[1]
def order(p):
    m=re.search(r"_(\d+)\.json$",p.name)
    return int(m.group(1)) if m else 0
paths=[ROOT/"data/assessments.json"]+sorted((ROOT/"data").glob("assessments_korea_addendum*.json"),key=order)
rows=[]
for p in paths:
    data=json.loads(p.read_text(encoding="utf-8"))
    if isinstance(data,list): rows.extend(data)
merged={}
for x in rows:
    merged[(x.get("plant_id"),x.get("species_group"))]=x
expected=list(merged.values())
actual=json.loads((ROOT/"data/public_assessments.json").read_text(encoding="utf-8"))
def canon(xs):
    return sorted(xs,key=lambda x:(x.get("plant_id",""),x.get("species_group","")))
if canon(expected)!=canon(actual):
    print(f"FAIL public_assessments drift: expected {len(expected)}, got {len(actual)}")
    sys.exit(1)
print(f"PASS public_assessments: {len(actual)} assessments / {len({x['plant_id'] for x in actual})} plants")
