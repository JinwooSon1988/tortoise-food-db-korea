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
# Known duplicates inside the legacy (non-released) source evidence files. The two copies differ, so picking
# one is an evidence-data decision, not a release fix. Ratchet: new duplicates fail, resolved ones must be removed.
LEGACY_DUPLICATE_EVIDENCE={"tortoise_table_spinach","tortoise_table_parsley","tortoise_table_radish"}
legacy_dups={eid for eid,n in Counter(ev_ids).items() if n>1}
for eid in sorted(legacy_dups-LEGACY_DUPLICATE_EVIDENCE): errs.append(f"duplicate evidence id {eid} x{Counter(ev_ids)[eid]}")
for eid in sorted(LEGACY_DUPLICATE_EVIDENCE-legacy_dups): errs.append(f"legacy duplicate {eid} is resolved; remove it from LEGACY_DUPLICATE_EVIDENCE")
ev=set(ev_ids)

# The released registry is data/public_assessments.json (+ data/public_evidence_records.json); the
# assessments*.json source files above no longer feed the site, so assessment checks run on the registry.
public_ev_ids=[e["id"] for e in load("public_evidence_records.json")["records"]]
for eid,n in Counter(public_ev_ids).items():
  if n>1: errs.append(f"public_evidence_records.json: duplicate evidence id {eid} x{n}")
public_ev=set(public_ev_ids)
ev|=public_ev
assessment_keys=[]; assessed_plants=set()
for r in load("public_assessments.json"):
  pid=r["plant_id"]
  if pid not in plants: errs.append(f"public_assessments.json: unknown plant {pid}")
  assessed_plants.add(pid)
  assessment_keys.append((pid,r.get("species_group","")))
  for eid in r.get("evidence_ids",[]):
    if eid not in public_ev: errs.append(f"public_assessments.json: missing evidence {eid}")
for key,n in Counter(assessment_keys).items():
  if n>1: errs.append(f"duplicate assessment key {key[0]}::{key[1]} x{n}")
public_rows=load("public_assessments.json")

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
# Blocked plants may appear in the registry only as conservative hold cards; they are not counted as assessed.
identity_blocked=set(coverage.get("identity_blocked_priority",[]))
evidence_blocked=set(coverage.get("evidence_blocked_priority",[]))
for r in public_rows:
  if r["plant_id"] in identity_blocked|evidence_blocked:
    if r.get("verdict") in ("supported_mixed_diet","limited_mixed_diet") or str(r.get("confidence","")).startswith(("A","B")):
      errs.append(f"{r['plant_id']}: blocked plant published above a conservative hold ({r.get('verdict')}, {r.get('confidence')})")
assessed_plants-=identity_blocked|evidence_blocked
expected=coverage.get("plants_with_explainable_assessment")
if expected!=len(assessed_plants): errs.append(f"coverage mismatch: declared {expected}, actual {len(assessed_plants)}")
if coverage.get("plant_master_count")!=len(plants): errs.append(f"plant master count mismatch: declared {coverage.get('plant_master_count')}, actual {len(plants)}")

# Every master plant must have exactly one review state: assessed, identity-blocked, or evidence-blocked.
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
