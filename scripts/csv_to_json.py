import csv, json, sys
from pathlib import Path
src=Path(sys.argv[1]); out=Path(sys.argv[2])
rows=[]
with src.open(encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        rows.append(r)
out.write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding="utf-8")
print(f"{len(rows)} rows -> {out}")
