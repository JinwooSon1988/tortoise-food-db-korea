from pathlib import Path
import json,glob,sys
ROOT=Path(__file__).resolve().parents[1]
queue=json.loads((ROOT/"data/plant_evidence_research_queue.json").read_text(encoding="utf-8"))
audit=queue.get("review_status",{})
rows=[]
for p in [ROOT/"data/assessments.json",*sorted((ROOT/"data").glob("assessments_korea_addendum*.json"))]:
    d=json.loads(p.read_text(encoding="utf-8"))
    if isinstance(d,list): rows.extend(d)
unresolved={"unresolved","insufficient_evidence","pending","unknown"}
errors=[]
for a in rows:
    if a.get("verdict") not in unresolved: continue
    pid=a.get("plant_id")
    r=audit.get(pid)
    if not r:
        errors.append(f"{pid}: public unresolved verdict has no research audit trail")
        continue
    done=set(r.get("tiers_completed",[]))
    remaining=set(r.get("remaining",[]))
    if not done:
        errors.append(f"{pid}: no completed evidence tier recorded")
    if not r.get("publication_blocker"):
        errors.append(f"{pid}: missing publication blocker")
    if done & remaining:
        errors.append(f"{pid}: evidence tiers appear in both completed and remaining")
if errors:
    print("FAIL: unresolved-publication audit")
    for e in errors: print("-",e)
    sys.exit(1)
print(f"PASS: unresolved-publication audit ({sum(1 for a in rows if a.get('verdict') in unresolved)} unresolved assessments)")
