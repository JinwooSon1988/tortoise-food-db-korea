from pathlib import Path
import json,sys
d=Path(__file__).resolve().parents[1]/"data"
plants={p["id"] for p in json.loads((d/"plants.json").read_text(encoding="utf-8"))}
ev={e["id"] for e in json.loads((d/"evidence.json").read_text(encoding="utf-8"))}
errs=[]
for fn in ["nutrition_records.json","assessments.json","evidence_map.json","restrictions.json","explanations.json"]:
    for r in json.loads((d/fn).read_text(encoding="utf-8")):
        if r["plant_id"] not in plants: errs.append(f"{fn}: unknown plant_id {r['plant_id']}")
for r in json.loads((d/"restrictions.json").read_text(encoding="utf-8")):
    if r["evidence_id"] not in ev: errs.append(f"restriction missing evidence {r['evidence_id']}")
for a in json.loads((d/"assessments.json").read_text(encoding="utf-8")):
    for eid in a["evidence_ids"]:
        if eid not in ev: errs.append(f"assessment missing evidence {eid}")
for n in json.loads((d/"nutrition_records.json").read_text(encoding="utf-8")):
    ca=n["values"].get("calcium_mg"); ph=n["values"].get("phosphorus_mg")
    if ca is not None and ph:
        calc=round(ca/ph,2)
        if calc!=n["derived"].get("ca_p_ratio"): errs.append(f"Ca:P mismatch {n['plant_id']}")
print("PASS" if not errs else "\n".join(errs))
sys.exit(1 if errs else 0)
