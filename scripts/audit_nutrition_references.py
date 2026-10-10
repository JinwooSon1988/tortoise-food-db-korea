#!/usr/bin/env python3
"""Validate reference-only nutrition without confusing it with primary values."""
import json
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data"

def read(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))

def main():
    reference = read("plant_nutrition_reference_v1.json")["records"]
    plants = {p["id"] for p in read("plants.json")}
    primary = {p["plant_id"] for p in read("plant_nutrition_v56.json")["plants"]}
    problems = []
    ids = set()
    allowed = {"related_part_reference", "related_species_reference", "dry_matter_reference"}
    for row in reference:
        rid = row.get("reference_id")
        pid = row.get("plant_id")
        if not rid or rid in ids:
            problems.append(f"duplicate/missing reference ID: {rid}")
        ids.add(rid)
        if pid not in plants:
            problems.append(f"{rid}: unknown plant {pid}")
        if row.get("status") != "reference_only" or row.get("feeding_verdict_use") is not False:
            problems.append(f"{rid}: reference must not change feeding verdict")
        if row.get("display_tier") not in allowed:
            problems.append(f"{rid}: unknown display tier")
        for field in ("source_name", "source_url", "scientific_name",
                      "analyzed_part", "preparation_state", "basis", "display_note_ko"):
            if not row.get(field):
                problems.append(f"{rid}: missing {field}")
        nutrients = row.get("nutrients", {})
        if not nutrients:
            problems.append(f"{rid}: no nutrients")
        for key, value in nutrients.items():
            if not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0:
                problems.append(f"{rid}: invalid {key}")
        if row.get("display_tier") != "dry_matter_reference" and "100" not in str(row.get("basis", "")):
            problems.append(f"{rid}: reference basis must be explicit per 100g")
        if pid in primary and row.get("display_tier") == "related_part_reference":
            # Permitted, but must remain reference-only rather than replacing primary.
            if row.get("status") != "reference_only":
                problems.append(f"{rid}: primary collision")
    print(json.dumps({"result": "PASS" if not problems else "FAIL",
                      "reference_records": len(reference),
                      "covered_plants": len({r["plant_id"] for r in reference}),
                      "errors": problems}, ensure_ascii=False, indent=2))
    return 1 if problems else 0

if __name__ == "__main__":
    raise SystemExit(main())
