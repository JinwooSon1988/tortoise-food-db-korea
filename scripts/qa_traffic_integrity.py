#!/usr/bin/env python3
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
plants=json.loads((ROOT/"data/plants.json").read_text(encoding="utf-8"))
public=[p for p in plants if p.get("identity_status")!="candidate_name"]
required=["1. 결론","2. 이 판정은 어디까지 적용되는가","3. 식물동정","4. 근거의 한계","탐색 링크:"]
for p in public:
    path=ROOT/"plant"/p["id"]/"index.html"
    if not path.exists(): raise SystemExit(f"missing generated page: {p['id']}")
    text=path.read_text(encoding="utf-8")
    for token in required:
        if token not in text: raise SystemExit(f"{p['id']}: missing {token}")
    if "동일한 급여 안전성·영양가·권장도를 뜻하지 않는다" not in text:
        raise SystemExit(f"{p['id']}: related-link safety boundary missing")
candidates=[p for p in plants if p.get("identity_status")=="candidate_name"]
for p in candidates:
    assert not (ROOT/"plant"/p["id"]/"index.html").exists(), f"candidate page must not be published: {p['id']}"
print("traffic integrity QA passed",len(public),"non-candidate records;",len(candidates),"candidates withheld")
