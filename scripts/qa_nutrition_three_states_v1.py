#!/usr/bin/env python3
"""Guard existing three-state nutrition classification against reference-only data loss."""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
load = lambda p: json.loads((root / p).read_text(encoding="utf-8"))
plants = load("data/plants.json")
refs = load("data/plant_nutrition_reference_v1.json")["records"]
verified = load("data/plant_nutrition_v56.json")["plants"]
plant_ids = {p["id"] for p in plants}
verified_ids = {r["plant_id"] for r in verified if r.get("verification_status") == "verified"}
reference_ids = set()
errors = []
seen = set()
for r in refs:
    pid = r.get("plant_id")
    rid = r.get("reference_id")
    if pid not in plant_ids:
        errors.append(f"unknown plant_id: {pid}")
    if not rid or rid in seen:
        errors.append(f"duplicate or empty reference_id: {rid}")
    seen.add(rid)
    if r.get("status") == "reference_only":
        if r.get("feeding_verdict_use") is not False:
            errors.append(f"{rid}: reference may not determine feeding verdict")
        if not r.get("source_url") or not r.get("analyzed_part") or not r.get("preparation_state"):
            errors.append(f"{rid}: source/part/preparation missing")
        reference_ids.add(pid)

def state(pid):
    if pid in verified_ids:
        return "검증된 영양자료"
    if pid in reference_ids:
        return "참고자료만 있음"
    return "연결 자료 없음"

for pid in reference_ids - verified_ids:
    if state(pid) != "참고자료만 있음":
        errors.append(f"{pid}: reference incorrectly hidden as no linked data")

if errors:
    raise SystemExit("\n".join(errors))
counts = {label: sum(state(pid) == label for pid in plant_ids) for label in
          ("검증된 영양자료", "참고자료만 있음", "연결 자료 없음")}
print(f"PASS: {len(plant_ids)} plants, {len(refs)} reference records; nutrition states {counts}")
