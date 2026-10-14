#!/usr/bin/env python3
"""Build the unit-2 research data sets from data/research/global_plant_evidence_transcription_v2.json.

Unit 2 only adds files. The v1 research files are read and never rewritten.

Writes, in data/research:
  global_evidence_sources_v2.json     sources read in unit 2, holds, and the status of every primary publication cited by unit-1 records
  tortoise_species_registry_v2.json   tortoise taxa added in unit 2 (GBIF name check)
  tortoise_plant_evidence_v2.json     evidence records added in unit 2
  primary_verification_ledger_v2.json one row per unit-1 evidence record: was the cited primary publication read, and what did it say
  plant_candidates_v2.json            cumulative candidate list over units 1 and 2
  forage_nutrition_research_v2.json   nutrient records added in unit 2 (study tables transcribed by hand, Feedipedia tables parsed)
  research_layer_summary_v2.json      counts for unit 1, unit 2 and the increase

Usage:
  python scripts/build_global_plant_evidence_research_v2.py --cache <dir of GBIF match responses> [--feedipedia-cache <dir>] [--offline]

No feeding grade is assigned anywhere. Names GBIF does not match exactly are left unresolved for review.
"""
import argparse
import importlib.util
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "data/research"
STATUS_BY_SOURCE_TYPE = {"peer_reviewed_field_study": "verified_primary_source", "peer_reviewed_captive_trial": "verified_primary_source",
                         "university_thesis_field_study": "verified_primary_source_thesis", "government_conservation_plan": "verified_review_document"}
EVIDENCE_CLASS_KO = {"wild_feeding_study": "야생 섭식 연구", "semi_wild_feeding_study": "자연 식생 울타리 안 섭식 연구", "captive_feeding_trial": "사육 급여 시험",
                     "local_knowledge": "현지 사냥꾼·주민 보고", "community_provisioning": "주민이 야생 개체에게 준 먹이", "conservation_plan_review": "보전계획 문헌 요약", "husbandry_practice": "사육 급여 관행"}
LIMIT = "Records what this tortoise taxon was reported to eat or be fed. It does not establish safe amounts, long-term outcomes or suitability for other tortoise species."


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    argv, sys.argv = sys.argv, ["x"]
    spec.loader.exec_module(m)
    sys.argv = argv
    return m


def homonyms(name, cache, offline, load, dump):
    """Backbone names spelled exactly like `name` when the plain match is ambiguous (the source gives no author)."""
    f = cache / (re.sub(r"[^A-Za-z0-9]+", "_", "Plantae_%s_verbose" % name).strip("_") + ".json")
    if f.exists():
        d = load(f)
    elif offline:
        return None
    else:
        url = "https://api.gbif.org/v1/species/match?" + urllib.parse.urlencode({"name": name, "kingdom": "Plantae", "verbose": "true"})
        d = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "tortoise-food-db-korea research"}), timeout=60))
        dump(f, d)
        time.sleep(0.4)
    out = []
    for alt in d.get("alternatives", []):
        if (alt.get("canonicalName") or "").lower() == name.lower() and alt.get("kingdom") == "Plantae":
            out.append({"scientific_name": alt.get("scientificName"), "status": alt.get("status"), "rank": alt.get("rank"),
                        "accepted_species": alt.get("species"), "family": alt.get("family")})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True)
    ap.add_argument("--feedipedia-cache")
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--nutrition-only", action="store_true",
                    help="rewrite only forage_nutrition_research_v2.json and the nutrition counts of the summary; the evidence file is left as it is")
    a = ap.parse_args()
    cache = Path(a.cache)
    cache.mkdir(parents=True, exist_ok=True)
    v1 = module(ROOT / "scripts/build_global_plant_evidence_research_v1.py", "build_v1")
    load, dump = v1.load, v1.dump
    tr1 = load(RES / "global_plant_evidence_transcription_v1.json")
    tr2 = load(RES / "global_plant_evidence_transcription_v2.json")
    ev1 = load(RES / "tortoise_plant_evidence_v1.json")["records"]
    cand1 = {c["candidate_key"]: c for c in load(RES / "plant_candidates_v1.json")["candidates"]}
    mix1 = load(RES / "enclosure_seed_mixtures_v1.json")["mixtures"]
    nut1 = load(RES / "forage_nutrition_research_v1.json")["records"]
    src1 = load(RES / "global_evidence_sources_v1.json")["sources"]
    reg1 = load(RES / "tortoise_species_registry_v1.json")["species"]
    plants = load(ROOT / "data/plants.json")

    by_species, by_genus = {}, {}
    for p in plants:
        sci = re.sub(r"\s+", " ", p["scientific"]).strip()
        m = re.match(r"([A-Z][a-z]+) (spp?\.|[a-z-]+)", sci)
        if not m:
            continue
        if m.group(2) in ("sp.", "spp."):
            by_genus.setdefault(m.group(1), []).append(p["id"])
        else:
            by_species.setdefault("%s %s" % (m.group(1), m.group(2)), []).append(p["id"])
            d = v1.gbif("%s %s" % (m.group(1), m.group(2)), "Plantae", cache, a.offline)
            if d and d.get("matchType") == "EXACT" and d.get("species") and p["id"] not in by_species.setdefault(d["species"], []):
                by_species[d["species"]].append(p["id"])

    tortoise_names = {t["tortoise_key"]: t["scientific_name"] for t in reg1}
    registry = []
    for key, t in tr2["tortoises_added"].items():
        d = v1.gbif(t["scientific_name"], "Animalia", cache, a.offline) or {}
        tortoise_names[key] = t["scientific_name"]
        registry.append({"tortoise_key": key, "scientific_name": t["scientific_name"], "common_name_ko": t["common_name_ko"], "common_name_en": t["common_name_en"],
                         "names_in_sources": t["names_in_sources"], "gbif_match_type": d.get("matchType"), "gbif_status": d.get("status"), "gbif_rank": d.get("rank"),
                         "gbif_usage_key": d.get("usageKey"), "gbif_accepted_name": d.get("species"), "family": d.get("family"),
                         "name_check": "accepted" if d.get("matchType") == "EXACT" and d.get("status") == "ACCEPTED" else
                         "kept_as_printed_gbif_status_%s" % str(d.get("status")).lower() if d.get("matchType") == "EXACT" else "needs_review"})

    resolved = {}
    overrides = {o["name"]: o for o in tr2.get("name_check_overrides", [])}

    def res(printed, queried=None):
        key = (printed, queried)
        if key not in resolved:
            r = v1.resolve(queried or printed, cache, a.offline)
            r["name_as_printed"], r["name_queried"] = printed, queried or printed
            if r["name_check"] == "not_resolved_needs_review":
                alts = homonyms(re.sub(r" (sp|spp)\.$", "", queried or printed), cache, a.offline, load, dump)
                if alts and len(alts) > 1:
                    r["name_check"] = "homonyms_in_backbone_author_not_given_needs_review"
                    r["backbone_homonyms"] = alts
            if printed in overrides:
                r.update(name_check=overrides[printed]["name_check"], accepted_name=None, accepted_key=None, name_check_reason=overrides[printed]["reason"],
                         backbone_suggestion_not_adopted=overrides[printed].get("backbone_suggestion"))
            resolved[key] = r
        return resolved[key]

    sources, evidence = [], []
    for sid, s in tr2["sources"].items():
        status = STATUS_BY_SOURCE_TYPE[s["source_type"]]
        sources.append({"source_id": sid, **{k: s[k] for k in ("citation", "url", "doi", "year", "language", "study_country", "publisher_country", "source_type",
                                                             "evidence_class", "method", "access", "what_was_read")},
                        "plant_record_count": len(s["records"]), "verification_status": status,
                        **{k: s[k] for k in ("rows_not_transcribed", "column_totals_checked", "rows_transcribed_from_table_2") if k in s}})
        printed_here = {row[1] for row in s["records"]}
        for i, row in enumerate(s["records"], 1):
            r = dict(zip(v1.COLUMNS, row))
            queried = row[12] if len(row) > 12 else None
            n = dict(res(r["plant_as_printed"], queried))
            if n["name_check"] == "synonym_of_accepted_name" and n["accepted_name"] in printed_here and n["accepted_name"] != r["plant_as_printed"]:
                # the source lists this name and the backbone's accepted name as two different plants: do not merge them
                n.update(name_check="synonym_in_backbone_but_source_lists_both_names_kept_separate", backbone_suggestion_not_adopted=n["accepted_name"], accepted_name=None)
            fam = re.match(r"family ([A-Z][a-z]+aceae)", r["note"] or "")
            cited = r["primary_reference_cited_by_source"]
            directness = ("reported_in_source_primary_not_read" if cited else
                          "statement_of_the_source_read" if s["source_type"] == "government_conservation_plan" else
                          "local_report_recorded_in_primary_study_read" if r["evidence_type"] == 6 else "primary_study_read")
            cls = ("husbandry_practice" if r["evidence_type"] == 5 else "community_provisioning" if r["evidence_type"] == 7 else "captive_feeding_trial" if r["wild_or_captive"] == "captive" else
                   "semi_wild_feeding_study" if r["wild_or_captive"] == "semi_wild" else
                   s["evidence_class"] if s["evidence_class"] in ("local_knowledge", "conservation_plan_review") else "wild_feeding_study")
            evidence.append({
                "evidence_id": "%s-%02d" % (sid, i), "unit": 2, "source_id": sid, "source_url": s["url"], "source_language": s["language"], "source_page": r["page"],
                "tortoise_key": r["tortoise_key"], "tortoise_scientific_name": tortoise_names[r["tortoise_key"]],
                "plant_name_as_printed": r["plant_as_printed"], "plant_name_queried": n["name_queried"], "plant_accepted_name": n["accepted_name"], "plant_family": n.get("family"),
                "plant_family_printed_by_source": fam.group(1) if fam else None,
                "family_differs_from_backbone": bool(fam and n.get("family") and fam.group(1) != n["family"]),
                "plant_name_check": n["name_check"], "plant_name_check_reason": n.get("name_check_reason"),
                "backbone_suggestion_not_adopted": n.get("backbone_suggestion_not_adopted"), "backbone_homonyms": n.get("backbone_homonyms"), "plant_rank_named_by_source": n["rank_named_by_source"], "plant_part": r["plant_part"], "preparation_state": r["offered_form"],
                "wild_or_captive": r["wild_or_captive"], "locality": r["locality"], "observed_consumption": r["consumption_signal"],
                "quantity_as_reported": r["quantity_as_reported"], "study_method": s["method"],
                "evidence_class": cls, "evidence_class_ko": EVIDENCE_CLASS_KO[cls],
                "evidence_type": {**v1.EVIDENCE_TYPES, 7: "food_given_by_local_people_observed"}[r["evidence_type"]], "evidence_directness": directness, "primary_reference_cited_by_source": cited,
                "is_negative_record": bool(re.search(r"avoid|reject", r["consumption_signal"])),
                "applies_to_other_tortoise_species": "not established by this source",
                "limitations": LIMIT + (" " + r["note"][0].upper() + r["note"][1:] + "." if r["note"] else ""),
                "verification_status": status, "feeding_grade": None})

    # ledger: every unit-1 evidence record against the primary publication it cites
    v2_by_plant = {(e["source_id"], e["plant_name_as_printed"]): e["evidence_id"] for e in evidence if e["tortoise_key"] != "elongata" or e["source_id"] != "platt_2001_shwe_settaw"}
    checked = {x["v1_evidence_id"]: x for x in tr2["primary_verification_of_v1_records"]}
    cited_status = {x["cited_as"]: x for x in tr2["cited_primary_status"]}
    primary_read = [e for e in ev1 if e["evidence_directness"] == "primary_study_read"] + [e for e in evidence if e["evidence_directness"] == "primary_study_read"]
    ledger = []
    for e in ev1:
        row = {"v1_evidence_id": e["evidence_id"], "tortoise_scientific_name": e["tortoise_scientific_name"], "plant_name_as_printed": e["plant_name_as_printed"],
               "directness_in_unit_1": e["evidence_directness"], "primary_reference_cited_by_source": e["primary_reference_cited_by_source"]}
        if e["evidence_id"] in checked:
            c = checked[e["evidence_id"]]
            row.update(status_after_unit_2=c["result"], primary_source_id=c["primary_source_id"],
                       v2_evidence_id=v2_by_plant.get((c["primary_source_id"], c["v2_record_plant"])) if c["v2_record_plant"] else None, note=c["note"])
        elif e["evidence_directness"] == "primary_study_read":
            row.update(status_after_unit_2="primary_read_in_unit_1", primary_source_id=e["source_id"], v2_evidence_id=None, note=None)
        elif e["evidence_directness"] == "reported_in_account_primary_not_read":
            cs = cited_status.get(e["primary_reference_cited_by_source"], {})
            row.update(status_after_unit_2="secondary_citation_primary_not_read", primary_source_id=None, v2_evidence_id=None,
                       cited_primary_search_status=cs.get("status", "not_listed"), note=cs.get("note"))
        else:
            row.update(status_after_unit_2="statement_of_the_source_no_primary_cited", primary_source_id=None, v2_evidence_id=None, note=None)
        acc = e["plant_accepted_name"]
        row["independent_primary_records_same_tortoise_and_plant"] = sorted(
            p["evidence_id"] for p in primary_read
            if acc and p["plant_accepted_name"] == acc and p["tortoise_key"] == e["tortoise_key"] and p["source_id"] != e["source_id"] and p["evidence_id"] != row.get("v2_evidence_id"))
        ledger.append(row)

    # cumulative candidates
    cands = {}

    def touch(n, printed):
        key = n["accepted_name"] or "printed:" + printed
        c = cands.setdefault(key, {"candidate_key": key, "accepted_name": n["accepted_name"], "family": n.get("family"), "rank": n["rank_named_by_source"],
                                   "names_as_printed": [], "name_check": n["name_check"], "tortoise_taxa_with_records": [], "evidence_ids": [],
                                   "negative_record_only": None, "seed_mixture_ids": [], "existing_plant_ids": [], "existing_genus_level_plant_ids": [],
                                   "forage_nutrition_record_ids": [], "first_seen_in_unit": 2, "feeding_grade": None})
        if printed not in c["names_as_printed"]:
            c["names_as_printed"].append(printed)
        return c

    for key, c in cand1.items():
        cands[key] = {**{k: (list(v) if isinstance(v, list) else v) for k, v in c.items()}, "first_seen_in_unit": 1}
    for e in evidence:
        c = touch({"accepted_name": e["plant_accepted_name"], "family": e["plant_family"], "rank_named_by_source": e["plant_rank_named_by_source"],
                   "name_check": e["plant_name_check"]}, e["plant_name_as_printed"])
        c["evidence_ids"].append(e["evidence_id"])
        if e["tortoise_scientific_name"] not in c["tortoise_taxa_with_records"]:
            c["tortoise_taxa_with_records"].append(e["tortoise_scientific_name"])
    neg = {e["evidence_id"]: e["is_negative_record"] for e in ev1 + evidence}
    for c in cands.values():
        if c["evidence_ids"]:
            c["negative_record_only"] = all(neg[i] for i in c["evidence_ids"])
        acc = c["accepted_name"]
        if acc and c["rank"] == "species":
            c["existing_plant_ids"] = sorted(by_species.get(acc, []))
            c["existing_genus_level_plant_ids"] = sorted(by_genus.get(acc.split()[0], []))
        elif acc and c["rank"] == "genus":
            c["existing_genus_level_plant_ids"] = sorted(by_genus.get(acc, []))
        c["database_status"] = ("species_already_in_database" if c["existing_plant_ids"] else
                                "genus_level_record_in_database" if c["existing_genus_level_plant_ids"] else
                                "not_in_database" if c["rank"] in ("species", "genus") and acc else "unresolved_name_not_a_candidate")

    # nutrition: study tables transcribed by hand
    nutrition = []
    src_by_id = {s["source_id"]: s for s in sources}
    for t in tr2["nutrient_tables"]:
        n = res(t["analyzed_taxon"])
        s = src_by_id[t["source_id"]]
        nutrition.append({"record_id": t["table_id"], "source_name": s["citation"], "source_id": t["source_id"], "source_url": s["url"], "source_language": s["language"],
                          "source_kind": "study_table_transcribed_by_hand", "table_title_as_printed": t["table_title_as_printed"], "source_page": t["page"],
                          "analyzed_taxon": t["analyzed_taxon"], "analyzed_taxon_accepted_name": n["accepted_name"], "analyzed_taxon_name_check": n["name_check"],
                          "analyzed_part": t["analyzed_part"], "preparation_state": t["preparation_state"], "analytical_method": t["analytical_method"],
                          "values": [{"nutrient_name": v[0], "nutrient_value": v[1], "nutrient_unit": v[2], "measurement_basis": v[3], "sample_count": v[4]} for v in t["values"]],
                          **{k: t[k] for k in ("basis_note", "sample_count_note") if k in t},
                          "excluded_from_this_record": t["excluded_from_this_record"], "use_limits": t["use_limits"],
                          "match_to_candidate": "same_taxon_name_as_an_evidence_record", "verification_status": "transcribed_by_hand_from_source_table", "feeding_verdict_use": False})
    # nutrition: Feedipedia tables for candidate species
    sel_path = RES / "forage_table_selection_v2.json"
    if sel_path.exists() and a.feedipedia_cache:
        v = module(ROOT / "scripts/verify_nutrition_reference_sources_v1.py", "verify_ref")
        vrow = module(ROOT / "scripts/verify_forage_nutrition_v5.py", "verify_rows")
        for t in load(sel_path)["tables"]:
            page = Path(a.feedipedia_cache) / ("feedipedia_%s.html" % t["node"])
            if not page.exists():
                continue
            rows, title = v.parse_feedipedia(page.read_text(encoding="utf-8", errors="replace"))
            if not title or not rows:
                continue
            listed = t["table_name_in_datasheet"]
            low = listed.lower()
            state = ("hay" if "hay" in low else "fresh" if "fresh" in low else "dried" if re.search(r"dehydrated|dried|dry\b", low) else
                     "crop_residue" if re.search(r"straw|haulm|stover", low) else "not_stated")
            n = res(t["taxon"])
            same = t["match"] == "same_species"
            values = [{"nutrient_name": lab, "nutrient_value": avg, "nutrient_unit": {"% as fed": "% as fed", "% dm": "% DM", "g/kg dm": "g/kg DM", "mg/kg dm": "mg/kg DM"}[unit],
                       "measurement_basis": "as fed" if unit == "% as fed" else "dry matter", "sample_count": nb}
                      for (lab, unit), (avg, nb) in rows.items() if lab in v1.COMPOSITION_LABELS and isinstance(nb, int) and unit in ("% as fed", "% dm", "g/kg dm", "mg/kg dm")]
            # the shared parser can take the sample count of the next row when a row's count is blank: keep a value only when an
            # independent read of its own table row shows the same mean and a printed sample count
            page_rows = vrow.page_rows(page.read_text(encoding="utf-8", errors="replace"))
            kept, dropped = [], []
            for val in values:
                h = [x for x in page_rows if x["label"].lower() == val["nutrient_name"] and x["unit"] == val["nutrient_unit"]]
                if len(h) == 1 and abs(h[0]["avg"] - val["nutrient_value"]) < 1e-9 and str(h[0]["nb"]) == str(val["sample_count"]):
                    kept.append(val)
                else:
                    dropped.append({"nutrient_name": val["nutrient_name"], "nutrient_unit": val["nutrient_unit"], "mean_on_page": h[0]["avg"] if len(h) == 1 else None,
                                    "sample_count_on_page": h[0]["nb"] if len(h) == 1 else None, "sample_count_from_the_shared_parser": val["sample_count"]})
            values = kept
            if not values:
                continue
            nutrition.append({"record_id": "feedipedia-%s" % t["node"], "source_name": "Feedipedia (INRAE, CIRAD, AFZ, FAO)", "source_id": str(t["node"]),
                              "values_dropped_no_sample_count_on_page": dropped,
                              "source_url": "https://www.feedipedia.org/node/%s" % t["node"], "source_language": "en", "source_kind": "compiled_feed_table_parsed",
                              "table_title_as_printed": listed, "table_note_on_page": None if title == listed or listed.endswith(title) else title, "source_page": None,
                              "analyzed_taxon": t["taxon"], "analyzed_taxon_accepted_name": n["accepted_name"], "analyzed_taxon_name_check": n["name_check"],
                              "analyzed_part": listed.split(",", 1)[1].strip() if "," in listed else "not stated", "preparation_state": state,
                              "analytical_method": "compiled feed table; average of the samples counted in sample_count", "values": values,
                              "excluded_from_this_record": "values the source marks as calculated (*) or prints without a sample count, and all ruminant, pig, poultry or rabbit energy and digestibility values",
                              "use_limits": "Livestock feed table. Not a tortoise digestibility or safety value. Fresh and hay tables come from different samples and must not be subtracted to estimate drying losses."
                                            + ("" if same else " Different species from the plant in the evidence record: kept as reference only and must not be shown as that plant's value."),
                              "match_to_candidate": t["match"], "reference_for_taxon": t.get("reference_for_taxon"), "part_note": t.get("part_note"), "verification_status": "transcribed_by_parser_from_cached_source_page", "feeding_verdict_use": False})
    v1_nut_ids = {r["record_id"] for r in nut1}
    nutrition = [r for r in nutrition if r["record_id"] not in v1_nut_ids]
    for r in nutrition:
        if r["match_to_candidate"] not in ("same_species", "same_taxon_name_as_an_evidence_record"):
            continue
        key = r["analyzed_taxon_accepted_name"] or "printed:" + r["analyzed_taxon"]
        if key in cands and r["record_id"] not in cands[key]["forage_nutrition_record_ids"]:
            cands[key]["forage_nutrition_record_ids"].append(r["record_id"])

    def cand_counts(cs):
        new = [c for c in cs if c["database_status"] == "not_in_database"]
        return {"plant_names": len(cs), "new_candidates_not_in_database": len(new), "new_candidates_species_level": sum(c["rank"] == "species" for c in new),
                "new_candidates_genus_level": sum(c["rank"] == "genus" for c in new),
                "species_already_in_database": sum(c["database_status"] == "species_already_in_database" for c in cs),
                "genus_level_record_in_database": sum(c["database_status"] == "genus_level_record_in_database" for c in cs),
                "unresolved_not_a_candidate": sum(c["database_status"] == "unresolved_name_not_a_candidate" for c in cs)}

    def ev_counts(es):
        return {"records": len(es), "by_tortoise": dict(sorted(Counter(e["tortoise_scientific_name"] for e in es).items())),
                "by_directness": dict(sorted(Counter(e["evidence_directness"] for e in es).items())),
                "by_wild_or_captive": dict(sorted(Counter(e["wild_or_captive"] for e in es).items())),
                "negative_records": sum(e["is_negative_record"] for e in es)}

    after = Counter(r["status_after_unit_2"] for r in ledger)
    state = Counter(r["preparation_state"] for r in nutrition)
    summary = {
        "unit_1": {"sources_with_plant_records": sum(1 for s in src1 if s["plant_record_count"]), "evidence": ev_counts(ev1), "candidates": cand_counts(list(cand1.values())),
                   "tortoise_taxa_with_evidence": len({e["tortoise_scientific_name"] for e in ev1}), "seed_mixtures": len(mix1),
                   "nutrition_records": len(nut1), "nutrition_values": sum(len(r["values"]) for r in nut1)},
        "unit_2_added": {"sources_with_plant_records": len(sources), "sources_by_language": dict(sorted(Counter(s["language"] for s in sources).items())),
                         "sources_by_study_country": dict(sorted(Counter(s["study_country"] for s in sources).items())),
                         "evidence": ev_counts(evidence), "evidence_by_class": dict(sorted(Counter(e["evidence_class"] for e in evidence).items())),
                         "tortoise_taxa_added_to_registry": len(registry), "seed_mixtures": 0,
                         "nutrition_records": len(nutrition), "nutrition_values": sum(len(r["values"]) for r in nutrition),
                         "nutrition_records_by_preparation_state": dict(sorted(state.items())),
                         "nutrition_records_by_source_kind": dict(sorted(Counter(r["source_kind"] for r in nutrition).items())),
                         "sources_on_hold": len(tr2["sources_on_hold"]), "seed_mixtures_on_hold": len(tr2["seed_mixtures_on_hold"])},
        "cumulative": {"evidence_records": len(ev1) + len(evidence), "tortoise_taxa_with_evidence": len({e["tortoise_scientific_name"] for e in ev1 + evidence}),
                       "candidates": cand_counts(list(cands.values())),
                       "primary_study_read_records": sum(e["evidence_directness"] == "primary_study_read" for e in ev1 + evidence)},
        "unit_1_records_after_primary_check": dict(sorted(after.items())),
        "unit_1_records_with_an_independent_primary_record": sum(bool(r["independent_primary_records_same_tortoise_and_plant"]) for r in ledger),
    }

    meta = {"schema_version": "2.0", "generated_by": "scripts/build_global_plant_evidence_research_v2.py", "generated_from": "data/research/global_plant_evidence_transcription_v2.json",
            "extends": "the v1 research files, which are not modified", "layer": "research_only_not_published", "grade_policy": v1.GRADE_POLICY}
    if a.nutrition_only:
        dump(RES / "forage_nutrition_research_v2.json", {**meta, "records": nutrition})
        old = load(RES / "research_layer_summary_v2.json")
        old["summary"]["unit_2_added"].update(nutrition_records=len(nutrition), nutrition_values=sum(len(r["values"]) for r in nutrition),
                                              nutrition_records_by_preparation_state=dict(sorted(Counter(r["preparation_state"] for r in nutrition).items())),
                                              nutrition_records_by_source_kind=dict(sorted(Counter(r["source_kind"] for r in nutrition).items())))
        dump(RES / "research_layer_summary_v2.json", old)
        print("unit 2 (nutrition only): nutrition records %d, values %d" % (len(nutrition), sum(len(r["values"]) for r in nutrition)))
        return
    dump(RES / "global_evidence_sources_v2.json", {**meta, "sources": sources, "cited_primary_status": tr2["cited_primary_status"], "holds_resolved_from_v1": tr2["holds_resolved_from_v1"],
                                                 "on_hold": tr2["sources_on_hold"], "seed_mixtures_on_hold": tr2["seed_mixtures_on_hold"]})
    dump(RES / "tortoise_species_registry_v2.json", {**meta, "name_authority": "GBIF backbone taxonomy, species/match API", "species_added": registry,
                                                   "names_in_sources_added_for_v1_taxa": tr2["tortoise_names_in_sources_added"]})
    dump(RES / "tortoise_plant_evidence_v2.json", {**meta, "records": evidence})
    dump(RES / "primary_verification_ledger_v2.json", {**meta, "note": "A record counts as checked only when the cited publication itself was read. An independent primary record is listed separately and does not verify the citation.", "records": ledger})
    dump(RES / "plant_candidates_v2.json", {**meta, "name_authority": "GBIF backbone taxonomy, species/match API", "scope": "cumulative over units 1 and 2",
                                          "candidates": sorted(cands.values(), key=lambda c: c["candidate_key"])})
    dump(RES / "forage_nutrition_research_v2.json", {**meta, "records": nutrition})
    dump(RES / "research_layer_summary_v2.json", {**meta, "summary": summary})
    print("unit 2: sources %d, tortoise taxa added %d, evidence %d, candidates (cumulative) %d, nutrition records %d"
          % (len(sources), len(registry), len(evidence), len(cands), len(nutrition)))


if __name__ == "__main__":
    main()
