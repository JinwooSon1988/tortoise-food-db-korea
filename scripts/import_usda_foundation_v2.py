from pathlib import Path
import csv,json,sys,re
if len(sys.argv)<3:
    raise SystemExit("Usage: python import_usda_foundation_v2.py <extracted_folder> <mapping.json>")
folder=Path(sys.argv[1]); mapping=json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
foodf=folder/"food.csv"; nf=folder/"nutrient.csv"; fnf=folder/"food_nutrient.csv"
for p in (foodf,nf,fnf):
    if not p.exists(): raise SystemExit(f"Missing {p.name}")
foods={}
with foodf.open(encoding="utf-8-sig",errors="replace") as f:
    for r in csv.DictReader(f): foods[r["fdc_id"]]=r
nut={}
with nf.open(encoding="utf-8-sig",errors="replace") as f:
    for r in csv.DictReader(f): nut[r["id"]]=r
wanted={"Water":"water_g","Protein":"protein_g","Total lipid (fat)":"fat_g","Fiber, total dietary":"fiber_g",
"Calcium, Ca":"calcium_mg","Phosphorus, P":"phosphorus_mg","Potassium, K":"potassium_mg","Sodium, Na":"sodium_mg",
"Sugars, Total":"sugars_g"}
vals={str(m["fdc_id"]):{} for m in mapping}
with fnf.open(encoding="utf-8-sig",errors="replace") as f:
    for r in csv.DictReader(f):
        fid=r.get("fdc_id")
        if fid not in vals: continue
        n=nut.get(r.get("nutrient_id"),{})
        key=wanted.get(n.get("name"))
        if key:
            try: vals[fid][key]=float(r["amount"])
            except: pass
out=[]
for m in mapping:
    fid=str(m["fdc_id"]); v=vals[fid]; ca=v.get("calcium_mg"); ph=v.get("phosphorus_mg")
    out.append({"plant_id":m["plant_id"],"food_description":foods.get(fid,{}).get("description"),
      "basis":"100 g edible portion","preparation":m.get("preparation","raw"),
      "source_provider":"USDA FoodData Central Foundation Foods","source_tier":"official_direct",
      "source_record_id":fid,"release":"2026-04","values":v,
      "derived":{"ca_p_ratio":round(ca/ph,2) if ca is not None and ph else None},
      "quality":{"status":"official_direct","mapping_reviewed":bool(m.get("reviewed"))}})
Path("usda_import_output.json").write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
print(f"Imported {len(out)} official records")
