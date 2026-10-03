#!/usr/bin/env python3
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
plants=json.loads((ROOT/"data/plants.json").read_text(encoding="utf-8"))
assessment_data=json.loads((ROOT/"data/public_assessments.json").read_text(encoding="utf-8"))
assessments=assessment_data if isinstance(assessment_data,list) else assessment_data.get("assessments",assessment_data.get("records",[]))
assessed_ids={a["plant_id"] for a in assessments}
public=[p for p in plants if p.get("identity_status")!="candidate_name" and p["id"] in assessed_ids]
required=["식물동정"]
for p in public:
    path=ROOT/"plant"/p["id"]/"index.html"
    if not path.exists(): raise SystemExit(f"missing generated page: {p['id']}")
    text=path.read_text(encoding="utf-8")
    for token in required:
        if token not in text: raise SystemExit(f"{p['id']}: missing {token}")
    # Unknowns are rendered from the current evidence model and need not use a fixed legacy heading.
    if not any(token in text for token in ("확인되지", "확정할 수 없", "정하지 않는다", "근거가 부족", "부위 미확인")):
        raise SystemExit(f"{p['id']}: missing explicit evidence limitation/unknown boundary")
    # Curated legacy pages may use their own heading structure; the content contract above is authoritative.
    related_boundary = (
        "동일한 급여 안전성·영양가·권장도를 뜻하지 않는다" in text
        or "급여 안전성·영양가·권장도가 같다는 뜻" in text
    )
    if not related_boundary:
        raise SystemExit(f"{p['id']}: related-link safety boundary missing")
candidates=[p for p in plants if p.get("identity_status")=="candidate_name"]
for p in candidates:
    assert not (ROOT/"plant"/p["id"]/"index.html").exists(), f"candidate page must not be published: {p['id']}"
print("traffic integrity QA passed",len(public),"non-candidate records;",len(candidates),"candidates withheld")
