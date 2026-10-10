#!/usr/bin/env python3
"""Ensure the international source queue reflects registered numeric references."""
import json
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data"

def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))

def main():
    queue = load("international_nutrition_reference_queue_20261010.json")
    references = load("plant_nutrition_reference_v1.json")["records"]
    plant_ids = {p["id"] for p in load("plants.json")}
    by_plant = {}
    reference_ids = set()
    duplicate_reference_ids = set()
    for item in references:
        rid = item.get("reference_id")
        if rid in reference_ids:
            duplicate_reference_ids.add(rid)
        reference_ids.add(rid)
        if item.get("nutrients") and item.get("status") == "reference_only":
            by_plant.setdefault(item["plant_id"], []).append(item["reference_id"])
    errors = [f"duplicate reference ID: {rid}" for rid in sorted(duplicate_reference_ids, key=str)]
    for item in references:
        if item.get("nutrients") and item.get("status") == "reference_only":
            if not isinstance(item.get("reference_id"), str) or not item["reference_id"].strip():
                errors.append(f"reference for {item.get('plant_id')}: missing reference ID")
            if item.get("plant_id") not in plant_ids:
                errors.append(f"reference for unknown plant: {item.get('plant_id')}")
    seen = set()
    for item in queue["records"]:
        pid = item["plant_id"]
        if pid in seen:
            errors.append(f"duplicate candidate plant: {pid}")
        seen.add(pid)
        if pid not in plant_ids:
            errors.append(f"unknown plant: {pid}")
        sources = item.get("candidate_sources")
        if not isinstance(sources, list) or not sources:
            errors.append(f"{pid}: candidate_sources must be nonempty")
        else:
            for index, source in enumerate(sources):
                if not isinstance(source, dict) or not all(
                    isinstance(source.get(field), str) and source[field].strip()
                    for field in ("institution", "record", "hold_reason")
                ):
                    errors.append(f"{pid}: candidate source {index} missing provenance or hold reason")
        if not isinstance(item.get("next_action"), str) or not item["next_action"].strip():
            errors.append(f"{pid}: missing next_action")
        actual = sorted(by_plant.get(pid, []))
        recorded = sorted(item.get("registered_reference_ids", []))
        if len(recorded) != len(set(recorded)):
            errors.append(f"{pid}: duplicate registered reference IDs")
        if actual != recorded:
            errors.append(f"{pid}: registered reference IDs differ; expected {actual}, got {recorded}")
        has_numeric = bool(actual)
        if item.get("reference_numeric_already_registered") is not has_numeric:
            errors.append(f"{pid}: numeric registration flag incorrect")
        expected_status = "reference_numeric_registered" if has_numeric else "source_candidate_only_no_numeric_transcription"
        if item.get("numeric_status") != expected_status:
            errors.append(f"{pid}: numeric status incorrect")
    counts = queue["counts"]
    expected = {"candidate_plants":len(seen),"pending_numeric_transcription":sum(not by_plant.get(p) for p in seen),"registered_numeric_reference_plants":sum(bool(by_plant.get(p)) for p in seen)}
    for key,value in expected.items():
        if counts.get(key) != value:
            errors.append(f"counts.{key}: expected {value}, got {counts.get(key)}")
    print(json.dumps({"result":"FAIL" if errors else "PASS",**expected,"errors":errors},ensure_ascii=False,indent=2))
    return bool(errors)

if __name__ == "__main__":
    raise SystemExit(main())
