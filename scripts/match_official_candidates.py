import json,sys,re
from pathlib import Path
records=json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
plants=json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
def norm(s):return re.sub(r"[\s,_\-()\[\]]","",str(s or "")).lower()
out=[]
for p in plants:
  terms=[p["canonical_ko"]]+p.get("aliases",[])
  for r in records:
    name=r.get("food_description","")
    score=0
    if norm(name)==norm(p["canonical_ko"]):score=100
    elif any(norm(t) and norm(t) in norm(name) for t in terms):score=70
    if score:
      out.append({"plant_id":p["plant_id"],"record_id":r.get("source_record_id"),
      "food_description":name,"score":score,"status":"manual_review_required"})
Path(sys.argv[3]).write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
print("candidates",len(out))
