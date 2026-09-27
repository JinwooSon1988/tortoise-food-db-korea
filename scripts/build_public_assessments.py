from pathlib import Path
import json,re
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"
OUT=DATA/"public_assessments.json"

def order(path):
    m=re.search(r"_(\d+)\.json$",path.name)
    return int(m.group(1)) if m else 0

paths=[DATA/"assessments.json"]+sorted(DATA.glob("assessments_korea_addendum*.json"),key=order)
merged={}
for path in paths:
    rows=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(rows,list):
        continue
    for row in rows:
        pid=row.get("plant_id")
        group=row.get("species_group")
        if pid and group:
            merged[(pid,group)]=row

rows=list(merged.values())
OUT.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(f"built {OUT.relative_to(ROOT)}: {len(rows)} assessments / {len({x['plant_id'] for x in rows})} plants from {len(paths)} source files")
