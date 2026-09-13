"""
Generic official nutrition CSV normalizer.
Input CSV headers are mapped via a JSON config. It does NOT decide plant identity.
Usage: python normalize_official_csv.py input.csv column_map.json output.json
"""
import csv,json,sys
from pathlib import Path
src=Path(sys.argv[1]); cfg=json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
out=[]
with src.open(encoding=cfg.get("encoding","utf-8-sig"),errors="replace") as f:
    for r in csv.DictReader(f):
        def g(k):
            col=cfg.get("columns",{}).get(k); return r.get(col) if col else None
        def num(k):
            x=g(k)
            if x in (None,"","-","N/A"): return None
            try:return float(str(x).replace(",",""))
            except:return None
        out.append({
          "source_record_id":g("record_id"),"food_description":g("food_name"),
          "preparation":g("preparation"),"basis_raw":g("basis"),
          "producer":g("producer"),
          "values":{"water_g":num("water_g"),"protein_g":num("protein_g"),
          "fiber_g":num("fiber_g"),"calcium_mg":num("calcium_mg"),
          "phosphorus_mg":num("phosphorus_mg"),"potassium_mg":num("potassium_mg"),
          "sodium_mg":num("sodium_mg"),"sugars_g":num("sugars_g")}
        })
Path(sys.argv[3]).write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
print("normalized",len(out),"records")
