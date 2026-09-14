from pathlib import Path
import json,sys
d=Path(__file__).resolve().parents[1]/"data"; errs=[]
plants={p["id"] for p in json.loads((d/"plants.json").read_text(encoding="utf-8"))}
evidence_files=["evidence.json","evidence_korea_addendum.json"]
ev=set()
for fn in evidence_files:
  p=d/fn
  if p.exists(): ev.update(e["id"] for e in json.loads(p.read_text(encoding="utf-8")))
record_files=["nutrition_records.json","assessments.json","assessments_korea_addendum.json","evidence_map.json","restrictions.json","explanations.json"]
for fn in record_files:
  p=d/fn
  if not p.exists(): continue
  for r in json.loads(p.read_text(encoding="utf-8")):
    if r["plant_id"] not in plants: errs.append(f"{fn}: unknown plant {r['plant_id']}")
    for eid in r.get("evidence_ids",[]):
      if eid not in ev: errs.append(f"{fn}: missing evidence {eid}")
for n in json.loads((d/"nutrition_records.json").read_text(encoding="utf-8")):
  if n.get("source_tier")=="official_direct" and not n.get("source_record_id"): errs.append(f"{n['plant_id']}: official_direct without record ID")
  ca=n["values"].get("calcium_mg"); ph=n["values"].get("phosphorus_mg")
  if ca is not None and ph and round(ca/ph,2)!=n["derived"].get("ca_p_ratio"): errs.append(f"{n['plant_id']}: Ca:P mismatch")
for r in json.loads((d/"restrictions.json").read_text(encoding="utf-8")):
  if r["evidence_id"] not in ev: errs.append(f"missing evidence {r['evidence_id']}")
print("PASS" if not errs else "\n".join(errs)); sys.exit(1 if errs else 0)
