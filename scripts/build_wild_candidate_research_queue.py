from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
st=json.loads((ROOT/"data/plant_expansion_staging.json").read_text(encoding="utf-8"))
risk=json.loads((ROOT/"data/wild_candidate_risk_screening.json").read_text(encoding="utf-8"))
wild=json.loads((ROOT/"data/wild_feeding_evidence.json").read_text(encoding="utf-8"))
risk_by={r["plant_id"]:r for r in risk.get("records",[])}
wild_ids={r.get("plant_id") for r in wild.get("records",[])}
rows=[]
for c in st.get("candidates",[]):
    cid=c["id"]; stage=c.get("stage"); rr=risk_by.get(cid,{})
    status=rr.get("status") or c.get("risk_status") or "not_screened"
    if stage=="needs_species_resolution":
        priority=1; bucket="species_resolution"; action="원자료에서 정확한 종명을 먼저 확정"
    elif stage=="taxonomy_verified":
        priority=2; bucket="toxicology_research"; action="종특이 독성·항영양·초식동물 안전자료 검색"
    elif status.startswith("blocked"):
        priority=3; bucket="conflicting_evidence"; action="상충 수의독성 근거를 해소할 Testudo/파충류 자료 검색"
    elif "research_gap" in status:
        priority=4; bucket="species_specific_gap"; action="정확한 종·부위의 위험성 자료 검색"
    elif stage=="evidence_researched":
        priority=5; bucket="assessment_blocker"; action="남은 publication blocker 해소 후 판정 가능성 재검토"
    else:
        priority=9; bucket="other"; action="상태 재검토"
    rows.append({"priority":priority,"plant_id":cid,"accepted_name":c.get("accepted_name"),"stage":stage,"risk_status":status,"has_direct_wild_record":cid in wild_ids,"bucket":bucket,"next_action":action,"publication_blocker":rr.get("publication_blocker") or c.get("publication_blocker")})
rows.sort(key=lambda x:(x["priority"],not x["has_direct_wild_record"],x["plant_id"]))
out={"schema_version":"1.0","generated_from":["plant_expansion_staging.json","wild_candidate_risk_screening.json","wild_feeding_evidence.json"],"rule":"낮은 priority 숫자부터 조사하되 안전성 blocker를 해소하기 전 공개 판정하지 않는다.","queue":rows}
(ROOT/"data/wild_candidate_research_queue.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("generated",len(rows),"research queue items")
