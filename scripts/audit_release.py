from pathlib import Path
import json,sys
from collections import Counter

d=Path(__file__).resolve().parents[1]/"data"; errs=[]
plant_rows=json.loads((d/"plants.json").read_text(encoding="utf-8")); plants={p["id"] for p in plant_rows}

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

# Every master plant must have exactly one review state: assessed, identity-blocked, or evidence-blocked.
identity_blocked=set(coverage.get("identity_blocked_priority",[]))
evidence_blocked=set(coverage.get("evidence_blocked_priority",[]))
for label,ids in (("identity_blocked_priority",identity_blocked),("evidence_blocked_priority",evidence_blocked)):
  unknown=ids-plants
  if unknown: errs.append(f"{label}: unknown plants {sorted(unknown)}")
for pid in sorted((identity_blocked|evidence_blocked)&assessed_plants):
  errs.append(f"review state conflict: {pid} is both assessed and blocked")
if identity_blocked&evidence_blocked:
  errs.append(f"review state conflict: blocked in both categories {sorted(identity_blocked&evidence_blocked)}")
reviewed=assessed_plants|identity_blocked|evidence_blocked
missing=plants-reviewed
if missing: errs.append(f"master plants without review state: {sorted(missing)}")
if len(reviewed)!=len(plants): errs.append(f"master review accounting mismatch: reviewed {len(reviewed)}, master {len(plants)}")

resolution_path=d/"blocked_food_resolution.json"
if identity_blocked or evidence_blocked:
  if not resolution_path.exists(): errs.append("blocked_food_resolution.json missing")
  else:
    rows=load("blocked_food_resolution.json"); resolution_ids=[r.get("plant_id") for r in rows]
    for pid,n in Counter(resolution_ids).items():
      if n>1: errs.append(f"duplicate blocked resolution {pid} x{n}")
    expected_blocked=identity_blocked|evidence_blocked
    actual_blocked=set(resolution_ids)
    if expected_blocked!=actual_blocked:
      errs.append(f"blocked resolution mismatch: expected {sorted(expected_blocked)}, actual {sorted(actual_blocked)}")
    for r in rows:
      pid=r.get("plant_id"); status=r.get("status")
      if pid in identity_blocked and status!="identity_blocked": errs.append(f"{pid}: expected identity_blocked resolution")
      if pid in evidence_blocked and status!="evidence_blocked": errs.append(f"{pid}: expected evidence_blocked resolution")
      if not r.get("reason") or not r.get("unlock_condition"): errs.append(f"{pid}: blocked resolution needs reason and unlock_condition")

print("PASS" if not errs else "\n".join(errs)); sys.exit(1 if errs else 0)
