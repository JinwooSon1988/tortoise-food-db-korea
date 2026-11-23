#!/usr/bin/env python3
"""Independent publication gate: exact species names must not be linked by genus alone."""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
plants = {p["id"]: p for p in json.loads((root / "data/plants.json").read_text(encoding="utf-8"))}
candidates = json.loads((root / "data/research/plant_candidates_v1.json").read_text(encoding="utf-8"))["candidates"]
errors = []
for candidate in candidates:
    if candidate["rank"] != "species" or candidate["name_check"] != "accepted":
        continue
    accepted = candidate["accepted_name"]
    for pid in candidate["existing_plant_ids"]:
        if pid not in plants:
            continue  # The core research QA reports unknown IDs.
        recorded = plants[pid]["scientific"].strip()
        if recorded.split()[:2] != accepted.split()[:2]:
            errors.append(f"{candidate['candidate_key']}: {accepted} linked to {pid} ({recorded})")
if errors:
    print("Exact species-link QA failed:")
    print("\n".join(errors))
    raise SystemExit(1)
print(f"Exact species-link QA passed for {len(candidates)} candidates")
