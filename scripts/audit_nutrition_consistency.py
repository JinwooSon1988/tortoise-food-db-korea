#!/usr/bin/env python3
"""Read-only nutrient integrity checks; no verdict or source data mutation."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "data"
def load(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))

def main():
    plants = {p["id"] for p in load("plants.json")}
    nutrients = load("plant_nutrition_v56.json")["plants"]
    holds = load("nutrition_hold_list_v1.json")["records"]
    audit = load("nutrition_coverage_audit_v1.json")
    errors = []
    nutrient_ids = [x["plant_id"] for x in nutrients]
    held_ids = [x["plant_id"] for x in holds]
    for label, ids in (("nutrition", nutrient_ids), ("holds", held_ids)):
        if len(ids) != len(set(ids)):
            errors.append(f"duplicate {label} plant IDs")
        unknown = set(ids) - plants
        if unknown:
            errors.append(f"unknown {label} IDs: {sorted(unknown)}")
    if set(nutrient_ids) & set(held_ids):
        errors.append("nutrition and hold registries overlap")
    if set(nutrient_ids) | set(held_ids) != plants:
        errors.append("nutrition and hold registries do not partition all plants")
    if len(nutrient_ids) != audit["verified_plants"] or len(held_ids) != audit["held_plants"]:
        errors.append("coverage summary count differs from actual registry")
    # Detect source identity and nutritional basis drift without inventing values.
    allowed_hold_reasons = {
        "subtype_ambiguous", "part_mismatch", "no_record_found",
        "genus_level_master", "policy_hold", "species_mismatch",
        "state_mismatch", "part_ambiguous",
    }
    for row in holds:
        if row.get("hold_reason_code") not in allowed_hold_reasons:
            errors.append(f"{row['plant_id']}: unknown nutrition hold reason")
        if row.get("do_not_infer") is not True:
            errors.append(f"{row['plant_id']}: nutrition hold must forbid inference")
    for row in nutrients:
        if row.get("verification_status") != "verified":
            errors.append(f"{row['plant_id']}: nutrition record not verified")
        if not row.get("source_name") or not row.get("source_id"):
            errors.append(f"{row['plant_id']}: source identity missing")
        if "100 g" not in str(row.get("basis", "")):
            errors.append(f"{row['plant_id']}: nutrition basis not per 100 g")
    numeric_fields = ("water_g", "protein_g", "fat_g", "carbohydrate_g", "fiber_g",
                      "calcium_mg", "phosphorus_mg", "potassium_mg", "sodium_mg",
                      "magnesium_mg", "iron_mg", "sugars_g", "vitamin_c_mg",
                      "vitamin_a_rae_ug", "energy_kcal")
    for row in nutrients:
        pid = row["plant_id"]
        for field in numeric_fields:
            val = row.get(field)
            if val is not None and (not isinstance(val, (int, float)) or isinstance(val, bool) or val < 0):
                errors.append(f"{pid}: invalid {field}={val}")
        ca, ph, ratio = (row.get("calcium_mg"), row.get("phosphorus_mg"),
                         row.get("calcium_phosphorus_ratio"))
        if all(isinstance(v, (int, float)) for v in (ca, ph, ratio)) and ph > 0:
            if abs(ca / ph - ratio) > 0.025:
                errors.append(f"{pid}: Ca:P ratio differs from source mineral amounts")
        if not row.get("source_url") or not row.get("plant_part") or not row.get("basis"):
            errors.append(f"{pid}: missing source URL, plant part or measurement basis")
    print(json.dumps({"result": "PASS" if not errors else "FAIL",
                      "verified": len(nutrient_ids), "held": len(held_ids),
                      "plants": len(plants), "errors": errors},
                     ensure_ascii=False, indent=2))
    return 1 if errors else 0

if __name__ == "__main__":
    raise SystemExit(main())
