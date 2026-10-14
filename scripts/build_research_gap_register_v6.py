#!/usr/bin/env python3
"""List the open research gaps of units 1-5 in one file: the unit-1 citations whose original was not read, and the plant names
that are still unresolved. Every plant stays listed; nothing is dropped for lack of evidence.

Reads the unit-3 ledger and cited-primary status, the unit-4 review queue, the unit-5 index and the unit-6 search log in this script.
Writes data/research/research_gap_register_v6.json. Offline.
"""
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "data/research"

# searches made in unit 6 (2026-10-14); a result is recorded only when the original was actually opened
SEARCHES_UNIT_6 = {
    "Longepierre and Grenot 1999": "one web search (French terms, Revue d'Ecologie / Persee); no copy of the article found",
    "Vijaya 1983; Ramesh and Parthasarathy 2006; Vasudevan et al. 2010": "one web search for Vijaya 1983: cited elsewhere as Hamadryad 8(3):11-13; the article itself was not found",
}
KIND = {"direct_feeding_observation": "direct feeding observation", "incidental_observation": "incidental observation", "fecal_detection": "fecal or seed detection",
        "fecal_macroscopic": "fecal detection (macroscopic)", "fecal_histological": "fecal detection (histological)", "fecal_dna_metabarcoding": "fecal detection (DNA)",
        "captive_feeding_record": "captive feeding record", "husbandry_recommendation": "husbandry recommendation or zoo/veterinary guideline",
        "zoo_feeding_practice_stated": "zoo feeding practice", "keeper_organisation_statement_method_not_given": "keeper organisation statement",
        "resident_or_hunter_report": "resident or hunter report", "secondary_citation_method_not_verified": "secondary citation, method not verified",
        "unreferenced_general_statement": "unreferenced general statement", "review_statement_method_not_given": "review statement",
        "account_or_review_statement_method_not_given": "species-account statement"}


def load(name):
    return json.loads((RES / name).read_text(encoding="utf-8"))


def main():
    ledger = load("primary_verification_ledger_v3.json")["records"]
    cited = {c["cited_as"]: c for c in load("global_evidence_sources_v3.json")["cited_primary_status"]}
    queue = load("review_queue_v4.json")["queue"]
    idx = {x["evidence_id"]: x for x in load("evidence_index_v5.json")["records"]}
    v5_names = [e for e in load("tortoise_plant_evidence_v5.json")["records"] if e["plant_name_check"].endswith("needs_review")]

    groups = defaultdict(list)
    for r in ledger:
        if r["status_after_unit_3"] == "secondary_citation_primary_not_read":
            groups[r["primary_reference_cited_by_source"]].append(r)
    citations = []
    for cit, rows in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        c = cited.get(cit, {})
        citations.append({
            "cited_as": cit, "records": len(rows), "evidence_ids": [r["v1_evidence_id"] for r in rows],
            "tortoise_species": sorted({r["tortoise_scientific_name"] for r in rows}),
            "plants_as_printed": sorted({r["plant_name_as_printed"] for r in rows}),
            "what_the_account_reports": "feeding stated in a species account that cites this publication; the kind of observation (direct, fecal, captive) is not verified",
            "original_status": "searched_unit_6_no_copy_found" if cit in SEARCHES_UNIT_6 else c.get("status", "not_listed"), "status_after_unit_3": c.get("status", "not_listed"), "original_note": c.get("note"), "unit_6_search": SEARCHES_UNIT_6.get(cit),
            "evidence_level_now": "secondary citation only; not a confirmed observation",
            "records_with_an_independent_primary_record": [r["v1_evidence_id"] for r in rows if r["independent_primary_records_same_tortoise_and_plant"]],
            "kept_in_database": True})

    names = []
    for n in queue["names_needing_review"]:
        xs = [idx[i] for i in n["evidence_ids"] if i in idx]
        names.append({
            "name_as_printed": n["name_as_printed"], "name_check": n["name_check"], "evidence_ids": n["evidence_ids"],
            "tortoise_species": sorted({x["tortoise"] for x in xs}), "species_specific": all(x["species_specific"] for x in xs),
            "plant_parts": sorted({x["plant_part"] for x in xs}), "evidence_kinds": sorted({KIND.get(m, m) for x in xs for m in x["detection_methods"]}),
            "any_on_hold": any(x["on_hold"] for x in xs), "unit": sorted({x["unit"] for x in xs}),
            "status": "kept with the name as printed; scientific name unresolved", "kept_in_database": True})
    for e in v5_names:
        names.append({"name_as_printed": e["plant_name_as_printed"], "name_check": e["plant_name_check"], "evidence_ids": [e["evidence_id"]],
                      "tortoise_species": [e["tortoise_scientific_name"]], "species_specific": True, "plant_parts": [e["plant_part"]],
                      "evidence_kinds": [KIND.get(m, m) for m in e["detection_methods"]], "any_on_hold": False, "unit": [5],
                      "status": "kept as the PDF text layer prints it; the scan is illegible, so the name is not resolved", "kept_in_database": True})

    doc = {"schema_version": "6.0", "generated_by": "scripts/build_research_gap_register_v6.py",
           "policy": "A plant is never removed for lack of evidence. Each gap states what is known, how it is known, and what is missing. Nothing here is a feeding grade or a safety statement.",
           "unit_1_citations_not_read": citations, "unresolved_plant_names": names,
           "totals": {"citation_groups": len(citations), "citation_records": sum(c["records"] for c in citations),
                      "citation_groups_by_status": {s: sum(1 for c in citations if c["original_status"] == s) for s in sorted({c["original_status"] for c in citations})},
                      "unresolved_names": len(names), "unresolved_names_unit_1_to_4": len(queue["names_needing_review"]), "unresolved_names_unit_5": len(v5_names)}}
    (RES / "research_gap_register_v6.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(doc["totals"], ensure_ascii=False))


if __name__ == "__main__":
    main()
