#!/usr/bin/env python3
"""Offline checks for the unit-6 verification files (Feedipedia sample counts, research gap register).

Fails when
  * a Feedipedia value kept in the research nutrition files (v1, v2, v5) is not 'matched' in the page audit (same label, unit,
    mean and sample count), or the audit is missing a kept value,
  * a value that the page audit found without a printed sample count is still kept, or is not listed as dropped in its record,
  * the unit-5 exclusion audit calls a row verified without the row's mean, a printed-or-not flag and the page it was read from,
    or its reason disagrees with the page audit,
  * the gap register loses a unit-1 citation that is still unread, loses an unresolved plant name, drops a plant, or calls an
    unread citation verified.
It never writes.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "data/research"


def load(name):
    return json.loads((RES / name).read_text(encoding="utf-8"))


def main():
    errors = []
    try:
        audit, gap = load("feedipedia_sample_count_audit_v6.json"), load("research_gap_register_v6.json")
        ex = load("forage_nutrition_exclusion_audit_v5.json")
    except Exception as e:  # noqa: BLE001
        report(["cannot read a unit-6 file: %s" % e])
    checked = {(x["file"], x["record_id"], x["nutrient_name"], x["nutrient_unit"]): x for x in audit["research_values"]}
    dropped_audit = {(x["file"], x["record_id"], x["nutrient_name"], x["nutrient_unit"]): x for x in audit["research_values_excluded"]}
    for f in ("forage_nutrition_research_v1.json", "forage_nutrition_research_v2.json", "forage_nutrition_research_v5.json"):
        for r in load(f)["records"]:
            if not r["record_id"].startswith("feedipedia-"):
                continue
            for v in r["values"]:
                x = checked.get((f, r["record_id"], v["nutrient_name"], v["nutrient_unit"]))
                if not x or x["status"] != "matched" or x["stored_value"] != v["nutrient_value"] or str(x["stored_nb"]) != str(v["sample_count"]):
                    errors.append("%s %s %s: kept value not matched against its source row" % (f, r["record_id"], v["nutrient_name"]))
            for dv in r.get("values_dropped_no_sample_count_on_page") or []:
                x = dropped_audit.get((f, r["record_id"], dv["nutrient_name"], dv["nutrient_unit"]))
                if not x or x["status"] != "excluded_nb_blank_on_page" or x.get("nb_on_page") is not None:
                    errors.append("%s %s %s: dropped value not confirmed as having no sample count on the page" % (f, r["record_id"], dv["nutrient_name"]))
    for k, x in dropped_audit.items():
        if x["status"] != "excluded_nb_blank_on_page":
            errors.append("%s: excluded value has status %s" % (k, x["status"]))
    expected_former = {("forage_nutrition_research_v2.json", "feedipedia-11865", "dry matter", "% as fed"), ("forage_nutrition_research_v2.json", "feedipedia-11865", "calcium", "g/kg DM"),
                       ("forage_nutrition_research_v5.json", "feedipedia-12645", "magnesium", "g/kg DM"), ("forage_nutrition_research_v5.json", "feedipedia-12645", "sodium", "g/kg DM"),
                       ("forage_nutrition_research_v5.json", "feedipedia-12646", "dry matter", "% as fed"), ("forage_nutrition_research_v5.json", "feedipedia-12646", "ether extract", "% DM")}
    if not expected_former <= set(dropped_audit):
        errors.append("the six values the former parser gave a wrong sample count are not all listed as excluded")
    for k, x in checked.items():
        if x.get("nb_on_page") is None and x["status"] == "matched":
            errors.append("%s: matched although the page prints no sample count" % (k,))
    for row in ex.get("excluded_values", []):
        if row.get("review_status") == "source_row_verified":
            x = dropped_audit.get(("forage_nutrition_research_v5.json", row["record_id"], row["nutrient_name"], row["nutrient_unit"]))
            if (not x or row.get("source_row_sample_count_printed") is not False or row.get("source_row_sample_count") != "" or row.get("source_row_mean") != x["mean_on_page"]
                    or row.get("exclusion_reason") != "source_row_prints_no_sample_count" or "sha256" not in str(row.get("verified_against"))):
                errors.append("exclusion audit %s %s: verified row disagrees with the page audit" % (row["record_id"], row["nutrient_name"]))

    ledger = load("primary_verification_ledger_v3.json")["records"]
    unread = sorted(r["v1_evidence_id"] for r in ledger if r["status_after_unit_3"] == "secondary_citation_primary_not_read")
    listed = sorted(i for c in gap["unit_1_citations_not_read"] for i in c["evidence_ids"])
    if listed != unread:
        errors.append("gap register: unread unit-1 citations differ from the ledger")
    for c in gap["unit_1_citations_not_read"]:
        if c["kept_in_database"] is not True or "not a confirmed observation" not in c["evidence_level_now"]:
            errors.append("gap register: citation %s must stay listed and must not be called confirmed" % c["cited_as"])
    q = {n["name_as_printed"] for n in load("review_queue_v4.json")["queue"]["names_needing_review"]}
    names = {n["name_as_printed"] for n in gap["unresolved_plant_names"]}
    if not q <= names or any(n["kept_in_database"] is not True for n in gap["unresolved_plant_names"]):
        errors.append("gap register: an unresolved name is missing or marked as removed")
    report(errors, "research layer unit-6 QA ok: %d kept Feedipedia values matched, %d excluded values without a printed sample count, %d unread citation records in %d groups, %d unresolved names"
           % (len(checked), len(dropped_audit), len(listed), len(gap["unit_1_citations_not_read"]), len(names)))


def report(errors, ok=None):
    if errors:
        print("research layer unit-6 QA failed (%d):" % len(errors))
        for e in errors[:80]:
            print(" -", e)
        sys.exit(1)
    if ok:
        print(ok)


if __name__ == "__main__":
    main()
