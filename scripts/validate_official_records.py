import json,sys,re
from pathlib import Path
p=Path(sys.argv[1])
rows=json.loads(p.read_text(encoding="utf-8"))
errors=[]
for i,r in enumerate(rows):
    if r.get("source_tier")!="official_direct": continue
    if not r.get("source_record_id"): errors.append(f"{i}: missing source_record_id")
    if not r.get("food_description"): errors.append(f"{i}: missing food_description")
    if r.get("basis")!="100 g edible portion": errors.append(f"{i}: unexpected basis")
    if not r.get("source_url"): errors.append(f"{i}: missing source_url")
    vals=r.get("values",{})
    if vals.get("calcium_mg") is not None and vals.get("phosphorus_mg"):
        expected=round(vals["calcium_mg"]/vals["phosphorus_mg"],2)
        if r.get("derived",{}).get("ca_p_ratio")!=expected: errors.append(f"{i}: Ca:P mismatch")
print("PASS" if not errors else "\n".join(errors))
sys.exit(1 if errors else 0)
