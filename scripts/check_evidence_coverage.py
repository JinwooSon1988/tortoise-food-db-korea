#!/usr/bin/env python3
"""Fail CI if catalog coverage counters do not agree; report progress toward 90%.

"Linked" (any feeding_evidence row) is NOT the same as "eaten". This report keeps the public catalog labels as they are
and adds a separate, explicit counting rule (COUNTING_RULE below):

  1. linked                 - at least one evidence row of any type
  2. consumption_supported  - at least one row that records the plant being eaten or fed (CONSUMPTION_TYPES)
  3. consumption_verified   - (2) with that row read in a full text (academic paper, review or guideline)
  4. reference_only         - linked, but no consumption row and no husbandry recommendation: only not-detected,
                              offered-not-eaten, toxicity, nutrition or taxonomy rows
  5. no_evidence            - no row at all
  husbandry_recommendation_only - linked through a care-sheet recommendation only (advice, not an observed feeding)

Consumption plants are also split by their best verification tier (academic full text > abstract > automatic
extraction > unverified literature lead > community/video report), so community and machine records are never
counted as checked research. Shards are read one at a time.

  python scripts/check_evidence_coverage.py [--catalog DIR] [--out reports/coverage_snapshot.json] [--audit-only]
"""
import argparse
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CONSUMPTION_TYPES = {"wild_feeding_observation", "captive_feeding_record", "community_report", "video_observation"}
RECOMMENDATION_TYPES = {"husbandry_recommendation"}
NON_CONSUMPTION_TYPES = {"wild_diet_not_detected", "offered_not_eaten", "toxicity", "nutrition", "taxonomy"}
# Same set the catalog builder and the taxon page call "checked in the original" (build_plant_catalog_v1.CHECKED_LEVELS).
FULL_TEXT_VERIFIED = ("full_text_verified", "full_text_named_not_extracted", "review_full_text_verified",
                      "guideline_full_text_verified", "reviewed_source_record")
# Best tier first; a plant is counted once, in the best tier any of its consumption rows reaches.
TIERS = [
    ("academic_full_text_verified", set(FULL_TEXT_VERIFIED)),
    ("abstract_checked", {"abstract_checked"}),
    ("auto_extracted_not_reviewed", {"full_text_auto_extracted"}),
    ("literature_lead_not_reverified", {"literature_lead_not_reverified"}),
    ("community_or_video_unverified", {"community_report_unverified", "video_observation_unverified"}),
]
COUNTING_RULE = {
    "consumption_types": sorted(CONSUMPTION_TYPES),
    "recommendation_types": sorted(RECOMMENDATION_TYPES),
    "non_consumption_types": sorted(NON_CONSUMPTION_TYPES),
    "full_text_verified_levels": list(FULL_TEXT_VERIFIED),
    "tiers": [name for name, _ in TIERS],
    "note": "wild_diet_not_detected and offered_not_eaten are evidence that the plant was NOT found eaten; they are never "
            "counted as consumption. No count here is a safety grade, and a record applies only to its tortoise taxon.",
}


def tier_of(rows):
    levels = {e.get("verification") for e in rows}
    for name, accepted in TIERS:
        if levels & accepted:
            return name
    raise AssertionError(f"verification levels without a tier: {sorted(levels)}")


def classify(record):
    """Semantic class of one catalog record (pure function, used by tests)."""
    evidence = record.get("feeding_evidence") or []
    types = {e.get("type") for e in evidence}
    consumption = [e for e in evidence if e.get("type") in CONSUMPTION_TYPES]
    unknown = sorted(t for t in types if t not in CONSUMPTION_TYPES | RECOMMENDATION_TYPES | NON_CONSUMPTION_TYPES)
    if not evidence:
        cls = "no_evidence"
    elif consumption:
        cls = "consumption_supported"
    elif types & RECOMMENDATION_TYPES:
        cls = "husbandry_recommendation_only"
    else:
        cls = "reference_only"
    return {
        "class": cls,
        "tier": tier_of(consumption) if consumption else None,
        "consumption_verified": any(e.get("verification") in FULL_TEXT_VERIFIED for e in consumption),
        "legacy_checked": any(e.get("verification") in FULL_TEXT_VERIFIED for e in evidence),
        "types": sorted(t for t in types if t),
        "unknown_types": unknown,
        "tortoise_taxa": sorted({e.get("tortoise") for e in consumption if e.get("tortoise")}),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalog", default=str(ROOT / "data/plant-catalog"))
    ap.add_argument("--out", help="also write the summary and per-class taxon lists to this JSON file")
    ap.add_argument("--audit-only", action="store_true", help="report a feeding-record status on reference-only plants instead of failing "
                    "(to measure an older catalog, e.g. main before this rule)")
    args = ap.parse_args()
    catalog = Path(args.catalog)
    idx = json.loads((catalog / "index.json").read_text(encoding="utf-8"))
    total = linked = checked = 0
    classes, tiers, types, unknown = Counter(), Counter(), Counter(), Counter()
    verified = 0
    legacy_label_mismatch = []   # research.status says "feeding record read in full text" but only not-eaten/reference rows exist
    reference_only, consumption_rows_by_tortoise = [], Counter()
    for shard in idx["shards"]:
        records = json.loads((catalog / shard["file"]).read_text(encoding="utf-8"))["records"]
        total += len(records)
        for r in records:
            evidence = r.get("feeding_evidence") or []
            c = classify(r)
            linked += bool(evidence)
            checked += c["legacy_checked"]
            classes[c["class"]] += 1
            verified += c["consumption_verified"]
            if c["tier"]:
                tiers[c["tier"]] += 1
            for t in c["types"]:
                types[t] += 1
            for t in c["unknown_types"]:
                unknown[t] += 1
            for t in c["tortoise_taxa"]:
                consumption_rows_by_tortoise[t] += 1
            if c["class"] == "reference_only":
                reference_only.append({"id": r.get("id"), "scientific": r.get("scientific"), "types": c["types"]})
            if (r.get("research") or {}).get("status") == "evidence_checked_in_full_text" and c["class"] == "reference_only":
                legacy_label_mismatch.append({"id": r.get("id"), "scientific": r.get("scientific"), "class": c["class"], "types": c["types"]})
    assert total == idx["count"], (total, idx["count"])
    assert linked == idx["counts"]["with_feeding_evidence"], (linked, idx["counts"]["with_feeding_evidence"])
    assert sum(classes.values()) == total
    assert not unknown, f"evidence types without a counting rule: {dict(unknown)}"
    assert args.audit_only or not legacy_label_mismatch, f"feeding-record research status on reference-only plants: {legacy_label_mismatch[:5]}"
    target = (total * 9 + 9) // 10
    consumption = classes["consumption_supported"]
    result = {
        "total_species": total,
        # Legacy keys (unchanged meaning): any linked row / any full-text-verified row of any type.
        "linked_species": linked, "source_checked_species": checked,
        "coverage_percent": round(100 * linked / total, 2), "target_90_percent": target,
        "remaining_to_target": max(0, target - linked),
        "semantic": {
            "1_linked_any_record": linked,
            "2_consumption_supported": consumption,
            "3_consumption_verified_in_full_text": verified,
            "4_reference_only_no_consumption": classes["reference_only"],
            "husbandry_recommendation_only": classes["husbandry_recommendation_only"],
            "5_no_evidence": classes["no_evidence"],
            "consumption_by_best_tier": dict(tiers),
            "consumption_verified_percent": round(100 * verified / total, 2),
            "remaining_to_target_by_verified_consumption": max(0, target - verified),
            "plants_by_evidence_type": dict(sorted(types.items())),
            "consumption_plants_by_tortoise_taxon_top20": dict(consumption_rows_by_tortoise.most_common(20)),
            "legacy_research_status_mismatch": len(legacy_label_mismatch),
        },
        "counting_rule": COUNTING_RULE,
        "note": "Evidence presence is not a safe-to-feed grade. Development branch only.",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        detail = dict(result, reference_only_taxa=reference_only, legacy_research_status_mismatch_taxa=legacy_label_mismatch)
        out.write_text(json.dumps(detail, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
