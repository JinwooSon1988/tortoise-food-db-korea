#!/usr/bin/env python3
import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
plants = {p["id"] for p in json.loads((ROOT/"data/plants.json").read_text(encoding="utf-8"))}
evidence_rows = json.loads((ROOT/"data/public_evidence_records.json").read_text(encoding="utf-8")).get("records", [])
evidence = {e["id"]: e for e in evidence_rows}

assessment_paths = [ROOT/"data/assessments.json"] + sorted(
    (ROOT/"data").glob("assessments_korea_addendum*.json")
)
rows = []
for path in assessment_paths:
    if not path.exists():
        continue
    data = json.loads(path.read_text(encoding="utf-8"))
    for row in data:
        rows.append((path.name, row))

errors = []
warnings = []
seen = set()
strong_verdicts = {"supported_mixed_diet", "safe_staple", "staple", "recommended"}
weak_directness = {"composition_only", "contextual", "related_taxon"}
hazard_re = re.compile(r"독성|독성물질|신장|간 손상|결석|갑상선|사포닌|옥살레이트|oxalate|goitrogen|glucosinolate", re.I)
hazard_evidence_re = re.compile(r"독성|tox|renal|kidney|liver|oxalat|goitrogen|glucosinolate|saponin|thyroid", re.I)

for filename, row in rows:
    pid = row.get("plant_id")
    group = row.get("species_group")
    key = (pid, group)
    if not pid or pid not in plants:
        errors.append(f"{filename}: unknown/missing plant_id {pid}")
    if not group:
        errors.append(f"{filename}:{pid}: missing species_group")
    if key in seen:
        errors.append(f"duplicate assessment key: {pid}|{group}")
    seen.add(key)

    ids = row.get("evidence_ids", [])
    if not isinstance(ids, list) or not ids:
        errors.append(f"{filename}:{pid}|{group}: evidence_ids must be a non-empty list")
        continue
    linked = []
    for eid in ids:
        ev = evidence.get(eid)
        if ev is None:
            errors.append(f"{filename}:{pid}|{group}: unresolved evidence_id {eid}")
            continue
        linked.append(ev)
        if pid not in ev.get("plant_ids", []):
            errors.append(f"{filename}:{pid}|{group}: evidence {eid} does not include plant_id {pid}")

    if linked and row.get("verdict") in strong_verdicts and all(e.get("directness") in weak_directness for e in linked):
        errors.append(f"{filename}:{pid}|{group}: strong verdict {row.get('verdict')} has no direct evidence")

    text = " ".join([str(row.get("why", ""))] + [str(x) for x in row.get("limits", [])])
    if linked and hazard_re.search(text):
        visible = " ".join(
            str(e.get(k, "")) for e in linked for k in ("source_title", "supports", "does_not_support")
        )
        if not hazard_evidence_re.search(visible):
            errors.append(f"{filename}:{pid}|{group}: hazard language is not visible in linked evidence")

used = {eid for _, row in rows for eid in row.get("evidence_ids", [])}
orphans = sorted(set(evidence) - used)
if orphans:
    warnings.append("orphan public evidence records: " + ", ".join(orphans))

if errors:
    raise SystemExit("Assessment evidence graph QA failed:\n- " + "\n- ".join(errors))
print(f"Assessment evidence graph QA passed: {len(rows)} assessments, {len(evidence)} public evidence records, {len(seen)} unique plant/group keys.")
for warning in warnings:
    print("WARNING:", warning)
