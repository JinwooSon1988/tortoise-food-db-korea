#!/usr/bin/env python3
import json, subprocess, sys
from pathlib import Path

R=Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R / "scripts"))
from public_verdict import public_plants

load=lambda p: json.loads((R/p).read_text(encoding="utf-8"))

# Rebuild first: the report itself must remain deterministic.
subprocess.check_call([sys.executable,str(R/"scripts/build_plant_coverage_gap_report_v1.py")])
d=load("data/plant_coverage_gap_report_v1.json")

# Canonical publication semantics live in public_verdict.public_plants().
plants=load("data/plants.json")
raw_assessments=load("data/public_assessments.json")
assessments=raw_assessments.get("assessments", raw_assessments.get("records", [])) if isinstance(raw_assessments,dict) else raw_assessments
canonical_ids={p["id"] for p in public_plants(plants, assessments)}
report_ids={x["plant_id"] for x in d["published_plants"]}
candidate_ids={x["plant_id"] for x in d["intake_candidates"]}

assert report_ids == canonical_ids, (
    "coverage published set drifted from canonical public_plants(): "
    f"missing={sorted(canonical_ids-report_ids)} extra={sorted(report_ids-canonical_ids)}"
)
assert d["summary"]["published_count"] == len(canonical_ids)
assert d["summary"]["research_pool_count"]==d["summary"]["published_count"]+d["summary"]["candidate_count"]
assert len(d["published_plants"])==d["summary"]["published_count"]
assert len(d["intake_candidates"])==d["summary"]["candidate_count"]
assert candidate_ids == ({p["id"] for p in plants} - canonical_ids)
assert report_ids.isdisjoint(candidate_ids)
assert all("gaps" in x and "next_action" in x for x in d["published_plants"])
assert all(x.get("published") is False for x in d["intake_candidates"])

print("OK",d["summary"])
