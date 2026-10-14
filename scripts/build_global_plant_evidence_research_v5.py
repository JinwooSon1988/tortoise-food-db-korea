#!/usr/bin/env python3
"""Build the unit-5 research data sets from data/research/global_plant_evidence_transcription_v5.json.

Unit 5 only adds files; the v1-v4 research files are read and never rewritten.

Writes, in data/research:
  global_evidence_sources_v5.json    sources read in unit 5, searches without a usable result, holds
  tortoise_plant_evidence_v5.json    evidence records added in unit 5, with detection methods
  forage_nutrition_research_v5.json  Feedipedia fresh and hay tables for forage plants (selection in forage_table_selection_v5.json)
  research_layer_summary_v5.json     counts, new plant names against the unit-4 candidate list, duplicate checks

Usage:
  python scripts/build_global_plant_evidence_research_v5.py --cache <GBIF cache dir> --feedipedia-cache <dir> [--offline]

No feeding grade is assigned anywhere.
"""
import argparse
import importlib.util
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "data/research"
STATUS_BY_SOURCE_TYPE = {"peer_reviewed_captive_study": "verified_primary_source", "zoo_information_page": "verified_zoo_statement"}
EVIDENCE_TYPES = {5: "captive_feeding_described_in_a_study", 8: "zoo_statement_or_guideline"}
LIMIT = "Records what this tortoise taxon was reported to eat or be fed. It does not establish safe amounts, long-term outcomes or suitability for other tortoise species."
COMMON = r"common names? only|common name as printed|local name only|food group only|plant group only|unidentified|not identified|not resolved"


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    argv, sys.argv = sys.argv, ["x"]
    spec.loader.exec_module(m)
    sys.argv = argv
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True)
    ap.add_argument("--feedipedia-cache", required=True)
    ap.add_argument("--offline", action="store_true")
    a = ap.parse_args()
    cache = Path(a.cache)
    v1 = module(ROOT / "scripts/build_global_plant_evidence_research_v1.py", "build_v1")
    v2 = module(ROOT / "scripts/build_global_plant_evidence_research_v2.py", "build_v2")
    v3 = module(ROOT / "scripts/build_global_plant_evidence_research_v3.py", "build_v3")
    load, dump = v1.load, v1.dump
    tr = load(RES / "global_plant_evidence_transcription_v5.json")
    cand4 = load(RES / "plant_candidates_v4.json")["candidates"]
    index4 = load(RES / "evidence_index_v4.json")["records"]
    old_sources = [s for i in (1, 2, 3, 4) for s in load(RES / ("global_evidence_sources_v%d.json" % i))["sources"]]
    names = {t["tortoise_key"]: t["scientific_name"] for t in load(RES / "tortoise_species_registry_v1.json")["species"]}

    sources, evidence = [], []
    for sid, s in tr["sources"].items():
        status = STATUS_BY_SOURCE_TYPE[s["source_type"]]
        sources.append({"source_id": sid, **{k: s[k] for k in ("citation", "url", "doi", "year", "language", "study_country", "publisher_country", "source_type",
                                                             "evidence_class", "method", "access", "what_was_read")}, "plant_record_count": len(s["records"]), "verification_status": status})
        for i, row in enumerate(s["records"], 1):
            r = dict(zip(v1.COLUMNS, row))
            n = dict(v1.resolve(r["plant_as_printed"], cache, a.offline))
            if n["name_check"] == "not_resolved_needs_review":
                alts = v2.homonyms(re.sub(r" (sp|spp)\.$", "", r["plant_as_printed"]), cache, a.offline, load, dump)
                if alts and len(alts) > 1:
                    n.update(name_check="homonyms_in_backbone_author_not_given_needs_review", backbone_homonyms=alts)
            if re.search(COMMON, r["note"] or "") and not n["name_check"].startswith("spelling"):
                n.update(accepted_name=None, family=None, name_check="common_name_only_not_resolved" if n["rank_named_by_source"] == "common_name_only" else "not_resolved_needs_review", backbone_homonyms=None)
            typ = r["evidence_type"]
            cls = "captive_feeding_trial" if typ == 5 else "institutional_husbandry_guideline"
            e = {"evidence_id": "%s-%02d" % (sid, i), "unit": 5, "source_id": sid, "source_url": s["url"], "source_citation": s["citation"], "source_language": s["language"], "source_page": r["page"],
                 "tortoise_key": r["tortoise_key"], "tortoise_scientific_name": names[r["tortoise_key"]], "species_specific": True,
                 "plant_name_as_printed": r["plant_as_printed"], "plant_accepted_name": n["accepted_name"], "plant_family": n.get("family"), "plant_name_check": n["name_check"],
                 "plant_rank_named_by_source": n["rank_named_by_source"], "backbone_homonyms": n.get("backbone_homonyms"), "gbif_fuzzy_candidate": n.get("gbif_fuzzy_candidate"),
                 "plant_part": r["plant_part"], "preparation_state": r["offered_form"], "wild_or_captive": r["wild_or_captive"], "locality": r["locality"],
                 "observed_consumption": r["consumption_signal"], "quantity_as_reported": r["quantity_as_reported"], "study_method": s["method"], "detection_methods": row[12],
                 "evidence_class": cls, "evidence_type": EVIDENCE_TYPES[typ], "evidence_directness": "husbandry_note_in_primary_source_read" if typ == 5 else "statement_of_the_source_read",
                 "primary_reference_cited_by_source": r["primary_reference_cited_by_source"], "is_negative_record": False, "negative_kind": None,
                 "applies_to_other_tortoise_species": "not established by this source",
                 "limitations": LIMIT + (" " + r["note"][0].upper() + r["note"][1:] + "." if r["note"] else ""), "verification_status": status, "feeding_grade": None}
            e["evidence_tier"] = v3.tier_of(e)
            evidence.append(e)

    # forage nutrient tables
    vref = module(ROOT / "scripts/verify_nutrition_reference_sources_v1.py", "verify_ref")
    sel = load(RES / "forage_table_selection_v5.json")
    accepted4 = {c["accepted_name"]: c["candidate_key"] for c in cand4 if c["accepted_name"]}
    nutrition = []
    for t in sel["tables"]:
        page = Path(a.feedipedia_cache) / ("feedipedia_%s.html" % t["node"])
        if not page.exists():
            continue
        rows, title = vref.parse_feedipedia(page.read_text(encoding="utf-8", errors="replace"))
        if not title or not rows:
            continue
        listed = t["table_name_in_datasheet"]
        low = listed.lower()
        state = "hay" if "hay" in low else "fresh" if "fresh" in low else "dried" if re.search(r"dehydrated|dried", low) else "not_stated"
        n = v1.resolve(t["taxon"], cache, a.offline)
        values = [{"nutrient_name": lab, "nutrient_value": avg, "nutrient_unit": {"% as fed": "% as fed", "% dm": "% DM", "g/kg dm": "g/kg DM", "mg/kg dm": "mg/kg DM"}[unit],
                   "measurement_basis": "as fed" if unit == "% as fed" else "dry matter", "sample_count": nb}
                  for (lab, unit), (avg, nb) in rows.items() if lab in v1.COMPOSITION_LABELS and isinstance(nb, int) and unit in ("% as fed", "% dm", "g/kg dm", "mg/kg dm")]
        if not values:
            continue
        vals = {(v["nutrient_name"], v["nutrient_unit"]): v for v in values}
        ca, ph = vals.get(("calcium", "g/kg DM")), vals.get(("phosphorus", "g/kg DM"))
        match = "same_species_as_a_candidate" if n["accepted_name"] in accepted4 else "forage_reference_only_species_not_named_in_any_evidence_record"
        nutrition.append({"record_id": "feedipedia-%s" % t["node"], "source_name": "Feedipedia (INRAE, CIRAD, AFZ, FAO)", "source_id": str(t["node"]),
                          "source_url": "https://www.feedipedia.org/node/%s" % t["node"], "table_title_as_printed": listed, "table_note_on_page": None if title == listed or listed.endswith(title) else title,
                          "analyzed_taxon": t["taxon"], "analyzed_taxon_accepted_name": n["accepted_name"], "analyzed_part": listed.split(",", 1)[1].strip() if "," in listed else ("hay" if "hay" in low else "not stated"),
                          "preparation_state": state, "analytical_method": "compiled feed table; average of the samples counted in sample_count", "values": values,
                          "calcium_to_phosphorus": ({"value": round(ca["nutrient_value"] / ph["nutrient_value"], 2), "derived_by_this_layer": True,
                                                     "caution": "A quotient of two table means computed here, not printed by the source; it describes this feed table only and is not a feeding rule."}
                                                    if ca and ph and ph["nutrient_value"] > 0 else None),
                          "excluded_from_this_record": "values marked as calculated (*) or printed without a sample count, silage tables, and all livestock energy and digestibility values",
                          "match_to_candidate": match, "candidate_key": accepted4.get(n["accepted_name"]), "why_selected": t["why_selected"],
                          "use_limits": "Livestock feed table. Not a tortoise digestibility or safety value. Fresh and hay tables come from different samples and must not be subtracted to estimate drying losses."
                                        + ("" if match.startswith("same_species") else " No evidence record names this species; the husbandry records that mention hay do not identify the grass, so this table is not that hay's value."),
                          "verification_status": "transcribed_by_parser_from_cached_source_page", "feeding_verdict_use": False, "feeding_grade": None})

    # duplicates against units 1-4 and new plant names
    old_urls = {s["url"] for s in old_sources}
    old_cit = {re.sub(r"\W+", "", s["citation"].lower())[:80] for s in old_sources}
    dup_sources = [s["source_id"] for s in sources if s["url"] in old_urls or re.sub(r"\W+", "", s["citation"].lower())[:80] in old_cit]
    seen_names = {x["plant_name_as_printed"] for x in index4} | {p for c in cand4 for p in c["names_as_printed"]}
    new_names = sorted({e["plant_name_as_printed"] for e in evidence} - seen_names)
    new_accepted = sorted({e["plant_accepted_name"] for e in evidence if e["plant_accepted_name"] and e["plant_accepted_name"] not in accepted4})
    summary = {
        "unit_5_added": {"sources_read": len(sources) + len(tr["sources_read_without_records"]), "sources_with_records": len(sources),
                         "sources_by_type": dict(sorted(Counter(s["source_type"] for s in sources).items())), "evidence_records": len(evidence),
                         "evidence_by_tier": dict(sorted(Counter(e["evidence_tier"] for e in evidence).items())),
                         "evidence_by_detection_method": dict(sorted(Counter(m for e in evidence for m in e["detection_methods"]).items())),
                         "evidence_by_wild_or_captive": dict(sorted(Counter(e["wild_or_captive"] for e in evidence).items())),
                         "plant_names_new_against_units_1_to_4": new_names, "accepted_species_new_against_units_1_to_4": new_accepted,
                         "nutrition_records": len(nutrition), "nutrition_values": sum(len(r["values"]) for r in nutrition),
                         "nutrition_by_state": dict(sorted(Counter(r["preparation_state"] for r in nutrition).items())),
                         "nutrition_by_match": dict(sorted(Counter(r["match_to_candidate"] for r in nutrition).items()))},
        "duplicate_check": {"sources_already_in_units_1_to_4": dup_sources, "nutrition_records_already_in_units_1_to_4": sorted(
            {r["record_id"] for r in nutrition} & {r["record_id"] for i in (1, 2) for r in load(RES / ("forage_nutrition_research_v%d.json" % i))["records"]})},
        "searches_without_a_usable_result": tr["searches_without_a_usable_result"], "gaps_not_filled": tr["gaps_not_filled"]}
    meta = {"schema_version": "5.0", "generated_by": "scripts/build_global_plant_evidence_research_v5.py", "generated_from": "data/research/global_plant_evidence_transcription_v5.json",
            "extends": "the v1-v4 research files, which are not modified", "layer": "research_only_not_published", "grade_policy": v1.GRADE_POLICY}
    dump(RES / "global_evidence_sources_v5.json", {**meta, "sources": sources, "sources_read_without_records": tr["sources_read_without_records"],
                                                 "searches_without_a_usable_result": tr["searches_without_a_usable_result"]})
    dump(RES / "tortoise_plant_evidence_v5.json", {**meta, "records": evidence})
    dump(RES / "forage_nutrition_research_v5.json", {**meta, "records": nutrition})
    dump(RES / "research_layer_summary_v5.json", {**meta, "summary": summary})
    print("unit 5: sources %d, evidence %d, new plant names %d, nutrition records %d, duplicate sources %d" % (len(sources), len(evidence), len(new_names), len(nutrition), len(dup_sources)))


if __name__ == "__main__":
    main()
