from pathlib import Path
import json, sys
ROOT=Path(__file__).resolve().parents[1]
d=json.loads((ROOT/"data/feeding_plans_v1.json").read_text(encoding="utf-8"))
plants={p["id"]:p for p in json.loads((ROOT/"data/plants.json").read_text(encoding="utf-8"))}
taxa={t["id"] for t in json.loads((ROOT/"data/animal_taxa_v1.json").read_text(encoding="utf-8"))["taxa"]}
evidence={e["id"] for e in json.loads((ROOT/"data/public_evidence_records.json").read_text(encoding="utf-8"))["records"]}
errors=[]
for plan in d["plans"]:
    if plan["taxon_id"] not in taxa: errors.append("unknown taxon "+plan["taxon_id"])
    if not plan.get("evidence_ids"): errors.append(plan["taxon_id"]+": missing evidence")
    for eid in plan.get("evidence_ids",[]):
        if eid not in evidence: errors.append(plan["taxon_id"]+": unknown evidence "+eid)
    for tier in plan.get("tiers",[]):
        if not tier.get("ko") or not tier.get("en") or not tier.get("note_ko") or not tier.get("note_en"):
            errors.append(plan["taxon_id"]+"/"+tier.get("id","?")+": bilingual guidance incomplete")
        for pid in tier.get("items",[]):
            p=plants.get(pid)
            if not p: errors.append("unknown plant "+pid)
            elif p.get("identity_status")=="candidate_name": errors.append("candidate plant exposed in plan "+pid)
if errors:
    print("FAIL: feeding plans")
    for e in errors: print("-",e)
    sys.exit(1)
print("PASS: feeding plans are bilingual, evidence-scoped, and candidate-safe")
