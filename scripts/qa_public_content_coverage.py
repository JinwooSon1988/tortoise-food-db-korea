#!/usr/bin/env python3
import json,pathlib,sys
P=pathlib.Path(__file__).resolve().parents[1]
plants=json.loads((P/"data/plants.json").read_text(encoding="utf-8"))
nut=json.loads((P/"data/plant_nutrition_v56.json").read_text(encoding="utf-8")).get("plants",[])
imgs=json.loads((P/"data/verified_plant_images_v56.json").read_text(encoding="utf-8")).get("images",[])
ids={x["id"] for x in plants}; nids={x["plant_id"] for x in nut}; iids={x["plant_id"] for x in imgs}
report={"plants":len(ids),"nutrition_verified":len(nids&ids),"nutrition_missing":len(ids-nids),"images_verified":len(iids&ids),"images_missing":len(ids-iids),"nutrition_coverage_pct":round(100*len(nids&ids)/len(ids),1),"image_coverage_pct":round(100*len(iids&ids)/len(ids),1),"nutrition_missing_ids":sorted(ids-nids),"image_missing_ids":sorted(ids-iids)}
out=P/"data/public_content_coverage.json";out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(report,ensure_ascii=False))
if len(nids&ids)<15: sys.exit("nutrition coverage regression")
if len(iids&ids)<8: sys.exit("image coverage regression")
