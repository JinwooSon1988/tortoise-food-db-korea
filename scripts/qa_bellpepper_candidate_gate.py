#!/usr/bin/env python3
"""Read-only gate: never allow unresolved bell-pepper candidates into verified nutrition."""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
nutrition = json.loads((root / "data/plant_nutrition_v56.json").read_text(encoding="utf-8"))
queue = json.loads((root / "data/nutrition_gap_workqueue_v3.json").read_text(encoding="utf-8"))
pepper = queue["batch_research_20261008"]["official_candidate_scan"]["bellpepper"]
candidates = pepper["records"]
assert len(candidates) == 4, "Expected four distinct color candidates"
assert {r["color"] for r in candidates} == {"green", "orange", "red", "yellow"}
assert len({r["ndb_number"] for r in candidates}) == 4
assert all(r["record_status"] == "NDB_verified_FDC_pending" for r in candidates)
assert all("fdc_id" not in r for r in candidates), "NDB number must not be labeled FDC ID"
promoted = [p for p in nutrition["plants"] if p["plant_id"] == "bellpepper"]
if promoted:
    assert all(p.get("verification_status") != "verified" for p in promoted), (
        "Bell pepper promoted while color-specific USDA identity is still unresolved"
    )
print("OK: 4 color-specific NDB candidates remain separate; no premature bellpepper verification")
