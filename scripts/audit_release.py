from pathlib import Path
import json,sys
from collections import Counter

d=Path(__file__).resolve().parents[1]/"data"; errs=[]
plants={p["id"] for p in json.loads((d/"plants.json").read_text(encoding="utf-8"))}

def load(fn):
  return json.loads((d/fn).read_text(encoding="utf-8"))

evidence_files=["evidence.json"]+[p.name for p in sorted(d.glob("evidence_korea_addendum*.json"))]
assessment_files=["assessments.json"]+[p.name for p in sorted(d.glob("assessments_korea_addendum*.json"))]

ev_ids=[]
for fn in evidence_files:
  ev_ids.extend(e["id"] for e in load(fn))
for eid,n in Counter(ev_ids).items():
  if n>1: errs.append(f"duplicate evidence id {eid} x{n}")
ev=set(ev_ids)

assessment_keys=[]; assessed_plants=set()
for fn in assessment_files:
  for r in load(fn):
    pid=r["plant_id"]
    if pid not in plants: errs.append(f"{fn}: unknown plant {pid}")
    assessed_plants.add(pid)
    key=(pid,r.get("species_group",""))
    assessment_keys.append(key)
    for eid in r.get("evidence_ids",[]):
      if eid not in ev: errs.append(f"{fn}: missing evidence {eid}")
for key,n in Counter(assessment_keys).items():
  if n>1: errs.append(f"duplicate assessment key {key[0]}::{key[1]} x{n}")

record_files=["nutrition_records.json","evidence_map.json","restrictions.json","explanations.json"]
for fn in record_files:
  p=d/fn
  if not p.exists(): continue
  for r in load(fn):
    if r["plant_id"] not in plants: errs.append(f"{fn}: unknown plant {r['plant_id']}")
    for eid in r.get("evidence_ids",[]):
      if eid not in ev: errs.append(f"{fn}: missing evidence {eid}")

for n in load("nutrition_records.json"):
  if n.get("source_tier")=="official_direct" and not n.get("source_record_id"): errs.append(f"{n['plant_id']}: official_direct without record ID")
  ca=n["values"].get("calcium_mg"); ph=n["values"].get("phosphorus_mg")
  if ca is not None and ph and round(ca/ph,2)!=n["derived"].get("ca_p_ratio"): errs.append(f"{n['plant_id']}: Ca:P mismatch")
for r in load("restrictions.json"):
  if r["evidence_id"] not in ev: errs.append(f"missing evidence {r['evidence_id']}")

coverage=load("coverage.json")
expected=coverage.get("plants_with_explainable_assessment")
if expected!=len(assessed_plants): errs.append(f"coverage mismatch: declared {expected}, actual {len(assessed_plants)}")
if coverage.get("plant_master_count")!=len(plants): errs.append(f"plant master count mismatch: declared {coverage.get('plant_master_count')}, actual {len(plants)}")

print("PASS" if not errs else "\n".join(errs)); sys.exit(1 if errs else 0)
