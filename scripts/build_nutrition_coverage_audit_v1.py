#!/usr/bin/env python3
"""Nutrition coverage audit for all public plants (descriptive only; never feeds verdicts).

Reads data/plants.json, data/plant_nutrition_v56.json and data/nutrition_hold_list_v1.json and writes
data/nutrition_coverage_audit_v1.json with per-plant status, per-field coverage, source-kind counts and the
legacy 69-plant baseline recomputed against the current registry.
"""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "nutrition_coverage_audit_v1.json"

FIELDS = ["water_g", "protein_g", "fat_g", "carbohydrate_g", "fiber_g", "sugars_g", "calcium_mg", "phosphorus_mg",
          "calcium_phosphorus_ratio", "potassium_mg", "sodium_mg", "magnesium_mg", "iron_mg", "vitamin_c_mg",
          "vitamin_a_rae_ug", "energy_kcal"]
# data/plants.json ids at commit 79c8948b (2026-09-20, docs/COVERAGE_EXPANSION_V1_QUEUE.md baseline "verified nutrition: 19/69").
# pea_shoot was later renamed to peashoot.
LEGACY_69 = ["chicory", "romaine", "lettuce", "radicchio", "endive", "dandelion", "sowthistle", "kale", "bokchoy", "mustard",
             "turnipgreens", "collard", "cabbage", "napa", "radishgreens", "broccolileaf", "cauliflowerleaf", "arugula", "plantain",
             "mulberry", "figleaf", "mallow", "hibiscusleaf", "hibiscusflower", "spinach", "beetgreens", "watercress", "parsley",
             "cilantro", "celeryleaf", "carrottop", "basil", "mint", "perilla", "clover", "alfalfa", "chickweed", "sweetpotatoleaf",
             "pumpkinleaf", "zucchini", "cucumber", "bellpepper", "tomato", "grapeleaf", "rose", "nasturtium", "pricklypear", "timothy",
             "orchard", "ryegrass", "wheatgrass", "barleygrass", "oatgrass", "cornleaf", "chrysanthemumleaf", "ssuk", "dolnamul", "minari",
             "aehobakleaf", "peashoot", "sunflowerleaf", "violet", "geranium", "pansy", "marigold", "calendula", "dill", "chard",
             "lambs_lettuce"]
LEGACY_BASELINE_VERIFIED = 19


def load(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def pct(n, d):
    return round(100 * n / d, 1) if d else 0.0


def main():
    plants = load("data/plants.json")
    ids = [p["id"] for p in plants]
    recs = {r["plant_id"]: r for r in load("data/plant_nutrition_v56.json").get("plants", []) if r.get("verification_status") == "verified"}
    holds = {r["plant_id"]: r for r in load("data/nutrition_hold_list_v1.json").get("records", [])}
    total = len(ids)
    field_cov = {f: {"plants": sum(1 for pid in ids if pid in recs and recs[pid].get(f) is not None)} for f in FIELDS}
    for f in field_cov:
        field_cov[f]["percent_of_public_plants"] = pct(field_cov[f]["plants"], total)
    per_plant = []
    for p in plants:
        pid = p["id"]
        r = recs.get(pid)
        row = {"plant_id": pid, "ko": p["ko"], "scientific": p["scientific"]}
        if r:
            present = [f for f in FIELDS if r.get(f) is not None]
            row.update({"status": "verified", "source_name": r["source_name"], "source_id": r["source_id"], "data_type": r["data_type"],
                        "source_kind": r.get("source_kind", "official_database"), "plant_part": r.get("plant_part"),
                        "preparation_state": r.get("preparation_state"), "fields_present": len(present), "fields_missing": [f for f in FIELDS if f not in present]})
        else:
            h = holds.get(pid)
            row.update({"status": "held", "hold_reason_code": h["hold_reason_code"] if h else None})
        per_plant.append(row)
    legacy_now = sum(1 for pid in LEGACY_69 if pid in recs)
    report = {
        "schema_version": "1.0",
        "purpose": "Descriptive nutrition coverage audit. Coverage numbers never change feeding verdicts, grades or confidence.",
        "public_plants": total,
        "verified_plants": len([pid for pid in ids if pid in recs]),
        "held_plants": len([pid for pid in ids if pid not in recs]),
        "coverage_percent": pct(len([pid for pid in ids if pid in recs]), total),
        "by_source_name": dict(sorted(Counter(recs[pid]["source_name"] for pid in ids if pid in recs).items())),
        "by_data_type": dict(sorted(Counter(recs[pid]["data_type"] for pid in ids if pid in recs).items())),
        "by_source_kind": dict(sorted(Counter(recs[pid].get("source_kind", "official_database") for pid in ids if pid in recs).items())),
        "hold_reasons": dict(sorted(Counter(holds[pid]["hold_reason_code"] for pid in ids if pid in holds).items())),
        "field_coverage": field_cov,
        "legacy_69_baseline": {"baseline_verified": LEGACY_BASELINE_VERIFIED, "baseline_source": "docs/COVERAGE_EXPANSION_V1_QUEUE.md (2026-09-20)",
                               "plants": len(LEGACY_69), "verified_now": legacy_now, "coverage_percent_now": pct(legacy_now, len(LEGACY_69)),
                               "still_held": [pid for pid in LEGACY_69 if pid not in recs]},
        "plants": per_plant,
    }
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"nutrition coverage: {report['verified_plants']}/{total} verified ({report['coverage_percent']}%), held {report['held_plants']}; "
          f"legacy 69: {legacy_now}/69")


if __name__ == "__main__":
    main()
