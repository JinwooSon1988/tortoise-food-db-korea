#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
d=json.loads((R/"data/plant_nutrition_v56.json").read_text())
by={x["plant_id"]:x for x in d["plants"]}
expected={"dandelion":"FDC 169226","pumpkinleaf":"FDC 169272","zucchini":"FDC 169291","chrysanthemumleaf":"FDC 169995","lambs_lettuce":"FDC 169219"}
for pid,fid in expected.items():
    x=by[pid]; assert x["source_id"]==fid and x["verification_status"]=="verified" and x["data_type"]=="SR Legacy"
    if x.get("calcium_mg") is not None and x.get("phosphorus_mg"):
        assert abs(x["calcium_phosphorus_ratio"]-round(x["calcium_mg"]/x["phosphorus_mg"],2))<0.001
q=json.loads((R/"data/nutrition_coverage_queue_v1.json").read_text())
assert not (set(expected)&{x["plant_id"] for x in q["records"]})
print("OK: 5 exact raw USDA SR Legacy records verified; queue reduced to",len(q["records"]))
