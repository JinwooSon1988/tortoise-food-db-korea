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
    dm_records = read("plant_nutrition_dm_basis_v1.json")["records"]
    dm_lookup = {(r["plant_id"], r["source_id"]): r for r in dm_records}
    problems = []
    ids = set()
    allowed = {"related_part_reference", "related_species_reference", "related_cultivar_reference", "dry_matter_reference"}
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
                      "reference_scope_ko", "source_verification",
                      "analyzed_part", "preparation_state", "basis", "display_note_ko"):
            if not row.get(field):
                problems.append(f"{rid}: missing {field}")
        if row.get("primary_eligible") is not False:
            problems.append(f"{rid}: reference cannot be promoted without review")
        if not str(row.get("source_url", "")).startswith("https://"):
            problems.append(f"{rid}: source must be HTTPS")
        nutrients = row.get("nutrients", {})
        units = row.get("nutrient_units", {})
        if any(k not in units for k in nutrients):
            problems.append(f"{rid}: missing per-nutrient unit")
        if not nutrients:
            problems.append(f"{rid}: no nutrients")
        for key, value in nutrients.items():
            if not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0:
                problems.append(f"{rid}: invalid {key}")
        # Reference studies may report fresh-mass g/kg or mg/kg, not only per 100g.\n        # Preserve source units; do not silently convert or relabel as per 100g.\n        if row.get("display_tier") != "dry_matter_reference" and not any(\n            token in str(row.get("basis", "")).lower()\n            for token in ("100", "g/kg", "mg/kg", "fresh mass", "fresh weight")\n        ):\n            problems.append(f"{rid}: reference basis lacks an explicit mass denominator")
        if row.get("origin_registry") == "data/plant_nutrition_dm_basis_v1.json":
            original = dm_lookup.get((pid, row.get("origin_source_id")))
            if original is None:
                problems.append(f"{rid}: missing original DM registry record")
            else:
                expected = {k: v["value"] for k, v in original["values"].items()}
                expected_n = {k: v["n"] for k, v in original["values"].items() if "n" in v}
                if nutrients != expected:
                    problems.append(f"{rid}: DM nutrient values differ from verified source registry")
                if row.get("sample_counts") != expected_n:
                    problems.append(f"{rid}: DM sample counts differ from source registry")
                for key in expected:
                    unit = "% as fed" if key == "dry_matter_pct_as_fed" else (
                        "g/kg DM" if key.endswith("_g_per_kg_dm") else "% DM")
                    if units.get(key) != unit:
                        problems.append(f"{rid}: unit mismatch for {key}")
                if row.get("preparation_state") != original.get("preparation_state"):
                    problems.append(f"{rid}: source state mismatch")
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
