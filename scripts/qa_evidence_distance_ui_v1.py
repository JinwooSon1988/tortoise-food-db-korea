#!/usr/bin/env python3
from pathlib import Path
import sys
root=Path(__file__).resolve().parents[1]
js=(root/"plant-detail-v56.js").read_text(encoding="utf-8")
css=(root/"plant-detail-v56.css").read_text(encoding="utf-8")
checks={
 "distance function":"function evidenceDistance(all)" in js,
 "exact taxon":"선택 종 직접 판정" in js,
 "same genus":"같은 Testudo속 근거 있음" in js,
 "tortoise general":"육지거북 일반 근거 있음" in js,
 "reptile general":"초식성 파충류 일반 근거 있음" in js,
 "not confirmed":"선택 종 판정 미확인" in js,
 "no auto transfer":"자동으로 급여 판정을 만들지 않는다" in js,
 "panel rendered":"distanceCard(distance)" in js,
 "responsive style":".v56-distance" in css,
}
bad=[k for k,v in checks.items() if not v]
if bad:
 print("FAIL: "+", ".join(bad)); sys.exit(1)
print("OK: evidence-distance UX preserves selected-species uncertainty and related-evidence tiers")
