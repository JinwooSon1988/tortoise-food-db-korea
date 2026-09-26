#!/usr/bin/env python3
import json, subprocess, sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
subprocess.check_call([sys.executable,str(R/"scripts/build_plant_coverage_gap_report_v1.py")])
d=json.loads((R/"data/plant_coverage_gap_report_v1.json").read_text(encoding="utf-8"))
assert d["summary"]["research_pool_count"]==d["summary"]["published_count"]+d["summary"]["candidate_count"]
assert len(d["published_plants"])==d["summary"]["published_count"]
assert len(d["intake_candidates"])==d["summary"]["candidate_count"]
assert all("gaps" in x and "next_action" in x for x in d["published_plants"])
assert all(x.get("published") is False for x in d["intake_candidates"])
committed=(R/"data/plant_coverage_gap_report_v1.json").read_text(encoding="utf-8")
# The build above is the canonical deterministic representation. Workflow-level git diff
# verifies that the committed artifact is synchronized.
print("OK",d["summary"])
