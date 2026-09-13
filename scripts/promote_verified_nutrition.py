from pathlib import Path
import json, sys
ROOT=Path(__file__).resolve().parents[1]
matrix=json.loads((ROOT/"data/ibera_verification_matrix.json").read_text(encoding="utf-8"))
staging=json.loads((ROOT/"data/near_complete_nutrition_candidates.json").read_text(encoding="utf-8"))
promoted=[]
errors=[]
for pid in ("dandelion","plantain"):
    accepted=[r for r in staging if r["plant_id"]==pid and r["state"]=="accepted"]
    if not accepted: continue
    for r in accepted:
        for k in ("record_id","source_url","food_description","preparation","basis","reviewer_note"):
            if not r.get(k): errors.append(f"{pid}: accepted record missing {k}")
        for k in ("calcium","phosphorus"):
            if r["nutrients"].get(k) is None: errors.append(f"{pid}: accepted record missing {k}")
    if not errors:
        m=next(x for x in matrix if x["plant_id"]==pid)
        m["official_nutrition_record"]="yes"
        m["blockers"]=[b for b in m["blockers"] if b!="official_nutrition"]
        m["completion"]=f"{4-len(m['blockers'])}/4"
        promoted.append(pid)
if errors:
    print("\n".join(errors));sys.exit(1)
(ROOT/"data/ibera_verification_matrix.json").write_text(json.dumps(matrix,ensure_ascii=False,indent=2),encoding="utf-8")
print("PASS; promoted:",promoted)
