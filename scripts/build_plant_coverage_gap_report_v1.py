#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
load=lambda p: json.loads((R/p).read_text(encoding="utf-8"))
plants=load("data/plants.json"); queue=load("data/plant_intake_queue_v1.json")["candidates"]
images={x["plant_id"] for x in load("data/verified_plant_images_v56.json").get("images",[])}
nutrition={x["plant_id"] for x in load("data/plant_nutrition_v56.json").get("plants",[]) if x.get("verification_status")=="verified"}
ev=load("data/public_evidence_records.json").get("records",[])
evidence_ids={pid for e in ev for pid in e.get("plant_ids",[])}
retail={x["plant_id"] for x in load("data/korean_retail_name_map.json")}
ass=[]
for p in ["data/assessments.json"]+[f"data/assessments_korea_addendum{'' if i==1 else '_'+str(i)}.json" for i in range(1,13)]:
    q=R/p
    if q.exists(): ass+=json.loads(q.read_text(encoding="utf-8"))
assmap={}
for a in ass: assmap.setdefault(a["plant_id"],[]).append(a)
rows=[]
for p in plants:
    pid=p["id"]; aa=assmap.get(pid,[])
    is_candidate=p.get("identity_status")=="candidate_name"
    exact=sorted({a.get("animal_taxon") for a in aa if a.get("assessment_scope")=="exact_species" and a.get("animal_taxon")})
    gaps=[]
    if p.get("identity_status") not in ("verified_name","verified"): gaps.append("identity")
    if pid not in images:gaps.append("image")
    if pid not in nutrition:gaps.append("nutrition")
    if not aa:gaps.append("assessment")
    if pid not in evidence_ids:gaps.append("evidence")
    if pid not in retail:gaps.append("korea_alias")
    rows.append({"plant_id":pid,"ko":p.get("ko"),"published":not is_candidate,"identity_status":p.get("identity_status"),"verified_image":pid in images,"verified_nutrition":pid in nutrition,"assessment_count":len(aa),"exact_species_taxa":exact,"evidence_record_present":pid in evidence_ids,"korea_alias_present":pid in retail,"gaps":gaps,"next_action":gaps[0] if gaps else "complete_current_schema"})
candidate_rows=[{"plant_id":x["id"],"ko":x.get("ko"),"published":False,"status":x.get("status"),"canonical_taxon_candidate":x.get("canonical_taxon_candidate"),"gaps":["identity","evidence","assessment"],"next_action":"identity"} for x in queue]
summary={"published_count":sum(r["published"] for r in rows),"candidate_count":sum(not r["published"] for r in rows)+len(queue),"research_pool_count":len(plants)+len(queue),"published":{"verified_image":sum(r["verified_image"] for r in rows),"verified_nutrition":sum(r["verified_nutrition"] for r in rows),"with_assessment":sum(r["assessment_count"]>0 for r in rows),"with_evidence":sum(r["evidence_record_present"] for r in rows),"with_korea_alias":sum(r["korea_alias_present"] for r in rows),"fully_complete_current_schema":sum(not r["gaps"] for r in rows)}}
out={"schema_version":"1.0","principle_ko":"coverage는 완성도 상태를 집계할 뿐 급여 안전성 점수나 식물 순위를 만들지 않는다.","summary":summary,"published_plants":rows,"intake_candidates":candidate_rows}
(R/"data/plant_coverage_gap_report_v1.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(summary,ensure_ascii=False))
