#!/usr/bin/env python3
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
plants=json.loads((ROOT/"data/plants.json").read_text(encoding="utf-8"))
assessment_data=json.loads((ROOT/"data/public_assessments.json").read_text(encoding="utf-8"))
assessments=assessment_data if isinstance(assessment_data,list) else assessment_data.get("assessments",assessment_data.get("records",[]))
assessed_ids={a["plant_id"] for a in assessments}
public=[p for p in plants if p.get("identity_status")!="candidate_name" and p["id"] in assessed_ids]
required=[]
for p in public:
    path=ROOT/"plant"/p["id"]/"index.html"
    if not path.exists(): raise SystemExit(f"missing generated page: {p['id']}")
    text=path.read_text(encoding="utf-8")
    for token in required:
        if token not in text: raise SystemExit(f"{p['id']}: missing {token}")
    # The focused detail UI must keep a visible evidence boundary without restoring retired accordions/related links.
    if not any(token in text for token in ("이 자료만으로는 알 수 없는 것", "확인되지", "확정할 수 없", "정하지 않는다", "근거가 부족", "부위 미확인", "적용할 수는 없다", "자동 적용하지 않는다")):
        raise SystemExit(f"{p['id']}: missing explicit evidence limitation/unknown boundary")
    if "비슷한 식물도 확인하기" in text or "적용 범위와 아직 확인되지 않은 내용 보기" in text:
        raise SystemExit(f"{p['id']}: retired detail UI returned")
candidates=[p for p in plants if p.get("identity_status")=="candidate_name"]
for p in candidates:
    assert not (ROOT/"plant"/p["id"]/"index.html").exists(), f"candidate page must not be published: {p['id']}"
print("traffic integrity QA passed",len(public),"non-candidate records;",len(candidates),"candidates withheld")
