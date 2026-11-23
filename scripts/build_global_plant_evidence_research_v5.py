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
    vrow = module(ROOT / "scripts/verify_forage_nutrition_v5.py", "verify_rows")

    def row_check(page_html, values):
        """Split values into those whose table row shows the same mean and the same sample count, and those whose row has no sample count."""
        rows = vrow.page_rows(page_html)
        keep, dropped = [], []
        for v in values:
            h = [x for x in rows if x["label"].lower() == v["nutrient_name"] and x["unit"] == v["nutrient_unit"]]
            if len(h) == 1 and abs(h[0]["avg"] - v["nutrient_value"]) < 1e-9 and str(h[0]["nb"]) == str(v["sample_count"]):
                keep.append(v)
            else:
                dropped.append({"nutrient_name": v["nutrient_name"], "nutrient_unit": v["nutrient_unit"], "mean_on_page": h[0]["avg"] if len(h) == 1 else None,
                                "sample_count_on_page": h[0]["nb"] if len(h) == 1 else None, "sample_count_from_the_shared_parser": v["sample_count"]})
        return keep, dropped

    nb_audit_earlier_units = []
    for f in ("forage_nutrition_research_v1.json", "forage_nutrition_research_v2.json"):
        for r in load(RES / f)["records"]:
            pg = Path(a.feedipedia_cache) / ("feedipedia_%s.html" % r["source_id"])
            if r["record_id"].startswith("feedipedia-") and pg.exists():
                _, bad = row_check(pg.read_text(encoding="utf-8", errors="replace"), r["values"])
                for b in bad:
                    nb_audit_earlier_units.append({"file": f, "record_id": r["record_id"], **b})
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
                  for (lab, unit), (avg, nb) in rows.items() if lab in v1.COMPOSITION_LABELS and v1.has_printed_sample_count(nb) and unit in ("% as fed", "% dm", "g/kg dm", "mg/kg dm")]
        values, dropped = row_check(page.read_text(encoding="utf-8", errors="replace"), values)
        dropped += [{"nutrient_name": lab, "nutrient_unit": {"% as fed": "% as fed", "% dm": "% DM", "g/kg dm": "g/kg DM", "mg/kg dm": "mg/kg DM"}[unit], "mean_on_page": avg, "sample_count_on_page": None,
                        "reason": "no sample count printed in the source row"}
                       for (lab, unit), (avg, nb) in rows.items() if lab in v1.COMPOSITION_LABELS and nb is None and unit in ("% as fed", "% dm", "g/kg dm", "mg/kg dm")]
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
                          "values_dropped_no_sample_count_on_page": dropped,
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
        "earlier_unit_feedipedia_values_whose_sample_count_is_not_on_the_page": nb_audit_earlier_units,
        "duplicate_check": {"sources_already_in_units_1_to_4": dup_sources, "nutrition_records_already_in_units_1_to_4": sorted(
            {r["record_id"] for r in nutrition} & {r["record_id"] for i in (1, 2) for r in load(RES / ("forage_nutrition_research_v%d.json" % i))["records"]})},
        "searches_without_a_usable_result": tr["searches_without_a_usable_result"], "gaps_not_filled": tr["gaps_not_filled"]}

    # cumulative index over units 1-5: which records may count as independent positive observations
    ledger = {r["v1_evidence_id"]: r for r in load(RES / "primary_verification_ledger_v3.json")["records"]}
    all_sources = {s["source_id"]: s for s in old_sources + sources}
    full = {e["evidence_id"]: e for i in (1, 2, 3, 4) for e in load(RES / ("tortoise_plant_evidence_v%d.json" % i))["records"]}
    full.update({e["evidence_id"]: e for e in evidence})

    def publication(sid):
        c = all_sources[sid]["citation"]
        m = re.match(r"\s*([^,.]+)", c)
        y = re.search(r"\b(1[89]\d\d|20\d\d)\b", c)
        return re.sub(r"\W+", "", (m.group(1) if m else c).lower()) + "_" + (y.group(1) if y else "nd")

    OBS = {"direct_feeding_observation", "incidental_observation", "fecal_macroscopic", "fecal_histological", "fecal_detection", "fecal_dna_metabarcoding",
           "direct_observation_and_fecal_analysis_not_separated"}
    history = {h["evidence_id"]: h["note"] for h in tr.get("animal_history_exclusions", [])}
    index5 = []
    for x in index4 + [{"evidence_id": e["evidence_id"], "unit": 5, "source_id": e["source_id"], "tortoise_key": e["tortoise_key"], "tortoise": e["tortoise_scientific_name"],
                        "species_specific": True, "plant_name_as_printed": e["plant_name_as_printed"], "plant_accepted_name": e["plant_accepted_name"], "plant_name_check": e["plant_name_check"],
                        "plant_part": e["plant_part"], "wild_or_captive": e["wild_or_captive"], "evidence_tier": e["evidence_tier"], "detection_methods": e["detection_methods"],
                        "evidence_directness": e["evidence_directness"], "is_negative_record": False, "on_hold": False, "quantity_as_reported": e["quantity_as_reported"]} for e in evidence]:
        led = ledger.get(x["evidence_id"], {})
        sup = led.get("confirming_evidence_id") if str(led.get("status_after_unit_3", "")).startswith("confirmed") else None
        obs = bool(set(x["detection_methods"]) & OBS)
        # the animal itself must be wild or semi-wild; an exception list alone (Lambert 1993) is not relied on
        counts = (x["evidence_id"] not in history and x["wild_or_captive"] in ("wild", "semi_wild") and not x["on_hold"] and not x["is_negative_record"] and not sup and x["evidence_tier"] in ("1_wild_feeding_study_read", "2_semi_wild_feeding_study_read") and obs
                  and x["evidence_directness"] == "primary_study_read")
        index5.append({k: x.get(k) for k in ("evidence_id", "unit", "source_id", "tortoise_key", "tortoise", "species_specific", "plant_name_as_printed", "plant_accepted_name",
                                             "plant_part", "wild_or_captive", "evidence_tier", "detection_methods", "evidence_directness", "is_negative_record", "on_hold", "quantity_as_reported")}
                      | {"publication_id": publication(x["source_id"]), "superseded_by": sup, "animal_history_note": history.get(x["evidence_id"]), "counts_as_independent_positive_wild_observation": counts,
                         "counts_as_captive_feeding_record": not x["on_hold"] and "captive_feeding_record" in x["detection_methods"],
                         "wild_statement_not_an_observation": x["wild_or_captive"] == "wild" and not obs})
    pubs = {}
    for s in all_sources:
        pubs.setdefault(publication(s), []).append(s)
    same_pub = {p: ids for p, ids in pubs.items() if len(ids) > 1}
    name_map = {}
    for x in index5:
        if x["plant_accepted_name"]:
            name_map.setdefault(x["plant_name_as_printed"], set()).add(x["plant_accepted_name"])
    name_conflicts = [{"plant_name_as_printed": n, "accepted_names": sorted(a)} for n, a in sorted(name_map.items()) if len(a) > 1]
    pairs = {}
    for x in index5:
        if x["counts_as_independent_positive_wild_observation"] and x["plant_accepted_name"]:
            pairs.setdefault((x["tortoise_key"], x["plant_accepted_name"]), set()).add(x["publication_id"])
    audit = {"publications_entered_as_more_than_one_source": [{"publication_id": p, "source_ids": ids} for p, ids in sorted(same_pub.items())],
             "printed_names_resolved_to_more_than_one_accepted_name": name_conflicts,
             "records_superseded_by_a_read_primary_record": sum(1 for x in index5 if x["superseded_by"]),
             "records_on_hold": [x["evidence_id"] for x in index5 if x["on_hold"]],
             "independent_positive_wild_observations": sum(x["counts_as_independent_positive_wild_observation"] for x in index5),
             "wild_statements_that_are_not_observations": [x["evidence_id"] for x in index5 if x["wild_statement_not_an_observation"]],
             "tortoise_plant_pairs_with_two_or_more_independent_publications": sum(1 for v in pairs.values() if len(v) > 1)}
    summary["cross_unit_audit"] = audit
    dump(RES / "evidence_index_v5.json", {"schema_version": "5.0", "generated_by": "scripts/build_global_plant_evidence_research_v5.py", "scope": "units 1-5",
                                         "note": "A record counts as an independent positive wild observation only when it is not on hold, not negative, not superseded by the primary record it cites, from a wild or semi-wild study that was read, and detected by observation or in faeces. Zoo, guideline and keeper statements never count, even when they describe the wild diet.",
                                         "records": index5})
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
