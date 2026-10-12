#!/usr/bin/env python3
"""Regression test: VERIFIED nutrition values must equal the values that were checked against the original sources.

data/nutrition_verified_source_check_v1.json is the ledger written by scripts/verify_verified_nutrition_sources_v1.py
after comparing every stored value with the original USDA CSV, RDA, MEXT, IFCT, BLS and journal files. This test
runs offline and fails when

  * a verified record is added or edited without re-running that comparison (value differs from the ledger, record
    missing from the ledger, or a nutrient field the ledger never compared),
  * a ledger entry is not a full match,
  * a Ca:P ratio does not follow from the stored calcium and phosphorus,
  * a verified record is not raw / per 100 g, or stores a nutrient without a unit,
  * a genus-level master (spp.) carries verified values without a documented Korean taxon mapping,
  * a REFERENCE record could be mistaken for a verified one, or is attached to a legacy alias ID.

It never changes data and never touches feeding verdicts.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NUTRIENT_KEY = re.compile(r"_(g|mg|ug|kcal)$|^dry_matter_pct$")
NOT_NUTRIENTS = {"calcium_phosphorus_ratio"}


def load(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def nutrients(rec):
    src = rec.get("values_per_100g") or rec
    return {k: float(v) for k, v in src.items() if NUTRIENT_KEY.search(k) and k not in NOT_NUTRIENTS
            and isinstance(v, (int, float)) and not isinstance(v, bool)}


def main():
    errors = []
    plants = {p["id"]: p for p in load("data/plants.json")}
    main_doc = load("data/plant_nutrition_v56.json")
    rda_doc = load("data/rda_food_composition_v56.json")
    ledger_doc = load("data/nutrition_verified_source_check_v1.json")
    ledger = {(r["table"], r["plant_id"], r["source_id"]): r for r in ledger_doc["records"]}
    mapping = {r["plant_id"]: r for r in load("data/korea_taxon_mapping_v1.json")["records"]}
    items = [("plants", r) for r in main_doc["plants"]] + [("part_state_records", r) for r in main_doc.get("part_state_records", [])] + \
            [("rda_food_composition_v56", r) for r in rda_doc["records"]]

    seen = set()
    for table, rec in items:
        pid, sid = rec["plant_id"], rec.get("source_id") or rec.get("rda_food_code")
        key = (table, pid, sid)
        seen.add(key)
        label = "%s/%s (%s)" % (table, pid, sid)
        if pid not in plants:
            errors.append(label + ": unknown plant id")
        entry = ledger.get(key)
        if not entry:
            errors.append(label + ": not in the source-verification ledger; run scripts/verify_verified_nutrition_sources_v1.py")
            continue
        if entry["status"] != "match":
            errors.append(label + ": ledger status is %s" % entry["status"])
        for k, v in nutrients(rec).items():
            f = entry["fields"].get(k)
            if not f:
                errors.append(label + ": %s was never compared with the original source" % k)
            elif abs(f["stored"] - v) > 1e-9:
                errors.append(label + ": %s is %s but the verified value is %s" % (k, v, f["stored"]))
            elif f["result"] not in ("exact", "rounded"):
                errors.append(label + ": %s ledger result is %s" % (k, f["result"]))
        vals = rec.get("values_per_100g") or rec
        ca, p, ratio = vals.get("calcium_mg"), vals.get("phosphorus_mg"), vals.get("calcium_phosphorus_ratio")
        if ratio is not None and (not ca or not p or abs(round(ca / p, 2) - ratio) > 0.011):
            errors.append(label + ": Ca:P ratio %s does not follow from Ca %s / P %s" % (ratio, ca, p))
        if table != "rda_food_composition_v56":
            if rec.get("verification_status") != "verified":
                errors.append(label + ": verification_status is %r" % rec.get("verification_status"))
            if "100 g" not in (rec.get("basis") or ""):
                errors.append(label + ": basis is not per 100 g")
            if rec.get("preparation_state") != "raw":
                errors.append(label + ": preparation_state is %r, verified records must be raw" % rec.get("preparation_state"))
            if not rec.get("plant_part"):
                errors.append(label + ": plant_part missing")
            if not rec.get("source_url") or not rec.get("source_id"):
                errors.append(label + ": source_url/source_id missing")
            if "units" in rec:
                for k in nutrients(rec):
                    if k not in rec["units"]:
                        errors.append(label + ": no unit recorded for %s" % k)
        if table == "plants" and pid in plants and plants[pid]["scientific"].strip().endswith("spp."):
            if not (mapping.get(pid) or {}).get("korea_taxon"):
                errors.append(label + ": genus-level master has verified values but no Korean taxon mapping in data/korea_taxon_mapping_v1.json")
    for key in sorted(set(ledger) - seen):
        errors.append("ledger entry without a record: %s/%s (%s)" % key)

    registry = load("data/plant_identity_registry_v1.json")
    legacy = {a["legacy_id"] for a in registry["canonical_aliases"]}
    verified_ids = {r["plant_id"] for r in main_doc["plants"]}
    for r in load("data/plant_nutrition_reference_v1.json")["records"]:
        rid = r.get("reference_id")
        if r.get("plant_id") not in plants:
            errors.append("reference %s: unknown plant id %s" % (rid, r.get("plant_id")))
        if r.get("plant_id") in legacy:
            errors.append("reference %s is attached to legacy alias id %s" % (rid, r["plant_id"]))
        if r.get("status") != "reference_only" or r.get("feeding_verdict_use") is not False or r.get("primary_eligible") is True:
            errors.append("reference %s must be reference_only, not primary and not used for verdicts" % rid)
        if r.get("verification_status") == "verified":
            errors.append("reference %s carries verification_status=verified" % rid)
        if not r.get("analyzed_part") or not r.get("basis") or not r.get("source_url"):
            errors.append("reference %s: analyzed_part, basis and source_url are required" % rid)
        for k in r.get("nutrients", {}):
            if k not in (r.get("nutrient_units") or {}):
                errors.append("reference %s: no unit for %s" % (rid, k))
    for pid in sorted(legacy & verified_ids):
        errors.append("verified nutrition record attached to legacy alias id %s" % pid)

    if errors:
        print("nutrition integrity QA failed (%d):" % len(errors))
        for e in errors:
            print(" -", e)
        sys.exit(1)
    print("nutrition integrity QA ok: %d verified records, %d values equal to the source-checked ledger"
          % (len(items), sum(len(nutrients(r)) for _, r in items)))


if __name__ == "__main__":
    main()
