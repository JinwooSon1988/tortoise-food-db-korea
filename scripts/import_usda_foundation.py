from pathlib import Path
import csv, sys, json, re
folder=Path(sys.argv[1]); query=sys.argv[2].lower()
files=[folder/"food.csv",folder/"nutrient.csv",folder/"food_nutrient.csv"]
if not all(p.exists() for p in files): raise SystemExit("food.csv, nutrient.csv, food_nutrient.csv 필요")
foods=[]
with files[0].open(encoding="utf-8-sig",errors="replace") as f:
    for r in csv.DictReader(f):
        d=(r.get("description") or "").lower()
        if all(t in d for t in re.findall(r"[a-z]+",query)): foods.append(r)
for r in foods[:20]: print(r.get("fdc_id"),r.get("description"),r.get("data_type"))
