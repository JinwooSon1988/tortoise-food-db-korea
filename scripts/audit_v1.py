from pathlib import Path
import json,sys
d=Path(__file__).resolve().parents[1]/"data"; e=[]
P=json.loads((d/"plants.json").read_text(encoding="utf-8")); ids={x["id"] for x in P}
for fn in ["assessments.json","evidence_map.json","restrictions.json","explanations.json","nutrition_records.json"]:
  for x in json.loads((d/fn).read_text(encoding="utf-8")):
    if x["plant_id"] not in ids:e.append(f"{fn}: bad plant_id {x['plant_id']}")
for x in json.loads((d/"nutrition_records.json").read_text(encoding="utf-8")):
  if x.get("source_tier")=="official_direct" and not x.get("source_record_id"):e.append("official record without ID")
  ca=x["values"].get("calcium_mg"); ph=x["values"].get("phosphorus_mg")
  if ca is not None and ph and round(ca/ph,2)!=x["derived"].get("ca_p_ratio"):e.append("Ca:P mismatch")
print("PASS" if not e else "\n".join(e));sys.exit(bool(e))
