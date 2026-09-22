#!/usr/bin/env python3
import json, math
from pathlib import Path
R=Path(__file__).resolve().parents[1]
d=json.loads((R/"data/plant_nutrition_part_state_v1.json").read_text(encoding="utf-8"))
plants={x["id"] for x in json.loads((R/"data/plants.json").read_text(encoding="utf-8"))}
rows=d.get("records",[])
assert d.get("schema_version")=="1.0"
assert rows
seen=set()
for x in rows:
    assert x["plant_id"] in plants
    assert x["part"] in {"whole","leaf","stem","flower","fruit","root","shoot","pad","other"}
    assert x["state"] in {"raw","dried","boiled","blanched","steamed","other"}
    assert x["verification_status"]=="verified"
    key=(x["plant_id"],x["source_id"])
    assert key not in seen; seen.add(key)
    ca=x.get("calcium_mg"); p=x.get("phosphorus_mg"); ratio=x.get("calcium_phosphorus_ratio")
    if ca is not None and p not in (None,0) and ratio is not None:
        assert abs(ratio-ca/p)<=0.02
generic={x["plant_id"] for x in json.loads((R/"data/plant_nutrition_v56.json").read_text(encoding="utf-8")).get("plants",[])}
assert "minari" not in generic, "part-state records must not silently promote generic minari nutrition"
print("OK",len(rows),"part/state nutrition records")
