#!/usr/bin/env python3
"""Build the unit-4 research data sets from data/research/global_plant_evidence_transcription_v4.json.

Unit 4 only adds files. The v1, v2 and v3 research files are read and never rewritten.

Writes, in data/research:
  global_evidence_sources_v4.json     sources read in unit 4, duplicate data sets, holds
  tortoise_species_registry_v4.json   non-specific tortoise groups used by unit-4 sources
  tortoise_plant_evidence_v4.json     evidence records added in unit 4, each with its detection methods
  plant_hazard_statements_v4.json     toxicity and oxalate statements made by unit-4 sources
  evidence_index_v4.json              every evidence record of units 1-4 in one list: tortoise, plant, part, tier, detection method, hold status
  plant_candidates_v4.json            cumulative candidate list
  review_queue_v4.json                everything that still needs a person: unread citations, unresolved names, conflicting records, holds
  research_layer_summary_v4.json      counts

Usage:
  python scripts/build_global_plant_evidence_research_v4.py --cache <GBIF cache dir> [--offline]

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
STATUS_BY_SOURCE_TYPE = {"peer_reviewed_field_study": "verified_primary_source", "university_thesis_field_study": "verified_primary_source_thesis",
                         "keeper_organisation_web_page": "verified_keeper_organisation_page", "veterinary_reference_text": "verified_veterinary_reference"}
STUDY_TYPES = ("peer_reviewed_field_study", "university_thesis_field_study")
EVIDENCE_TYPES = {1: "direct_study_of_this_tortoise_species", 8: "institutional_husbandry_guideline", 9: "keeper_organisation_statement"}
LIMIT = "Records what this tortoise taxon was reported to eat or be fed. It does not establish safe amounts, long-term outcomes or suitability for other tortoise species."
COMMON = r"common names? only|common name as printed|local name only|food group only|plant group only|unidentified|not identified"


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    argv, sys.argv = sys.argv, ["x"]
    spec.loader.exec_module(m)
    sys.argv = argv
    return m


def method_category(e, by_source):
    """One detection-method label for a record of units 1-3, which did not record the method per record."""
    direct, cls = e["evidence_directness"], e.get("evidence_class")
    text = "%s %s" % (e["plant_part"], e["observed_consumption"])
    if direct in ("reported_in_account_primary_not_read", "reported_in_source_primary_not_read"):
        return "secondary_citation_method_not_verified"
    if cls in ("institutional_husbandry_guideline",):
        return "husbandry_recommendation"
    if cls == "keeper_organisation_statement":
        return "keeper_organisation_statement_method_not_given"
    if cls == "community_provisioning":
        return "provisioned_food_observed"
    if cls == "local_knowledge" or e["evidence_type"] == "local_knowledge_report":
        return "resident_or_hunter_report"
    if cls in ("captive_feeding_trial", "husbandry_practice") or e["evidence_type"] in ("specialist_husbandry_practice", "husbandry_note_in_a_publication") or e["wild_or_captive"] == "captive":
        return "captive_feeding_record"
    if re.search(r"feces|faeces|dung|scat", text):
        return "fecal_detection"
    if e["source_id"] in by_source:
        return by_source[e["source_id"]]
    return "account_or_review_statement_method_not_given"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True)
    ap.add_argument("--offline", action="store_true")
    a = ap.parse_args()
    cache = Path(a.cache)
    v1 = module(ROOT / "scripts/build_global_plant_evidence_research_v1.py", "build_v1")
    v2 = module(ROOT / "scripts/build_global_plant_evidence_research_v2.py", "build_v2")
    v3 = module(ROOT / "scripts/build_global_plant_evidence_research_v3.py", "build_v3")
    load, dump = v1.load, v1.dump
    tr = load(RES / "global_plant_evidence_transcription_v4.json")
    old = [load(RES / ("tortoise_plant_evidence_v%d.json" % i))["records"] for i in (1, 2, 3)]
    cand3 = load(RES / "plant_candidates_v3.json")["candidates"]
    ledger3 = load(RES / "primary_verification_ledger_v3.json")["records"]
    res3 = load(RES / "plant_name_resolutions_v3.json")["resolutions"]
    corr3 = {c["evidence_id"]: c for c in load(RES / "record_corrections_v3.json")["corrections"]}
    held3 = {i: c for i, c in corr3.items() if c["action"] == "put_on_hold"}
    mg_labels = tr["moorhouse_method_labels"]

    def quantity_now(e):
        c = corr3.get(e["evidence_id"])
        return (None if c["action"] == "put_on_hold" else c["corrected_quantity"]) if c else e.get("quantity_as_reported")

    def methods_for(e):
        """Moorhouse-Gann 2022 records name their methods in the quantity text; read them from the corrected text only."""
        if e["evidence_id"] in held3:
            return ["not_determinable_record_on_hold"]
        q = quantity_now(e) or ""
        out = [mg_labels[lab] for lab, n in re.findall(r"(DNA metabarcoding|dung morphology|feeding observation) (\d+) of", q) if int(n) > 0]
        if "stated in the article text" in q:
            out.append("statement_in_article_text")
        return out
    plants = load(ROOT / "data/plants.json")

    names = {t["tortoise_key"]: t["scientific_name"] for t in load(RES / "tortoise_species_registry_v1.json")["species"]}
    names.update({t["tortoise_key"]: t["scientific_name"] for t in load(RES / "tortoise_species_registry_v2.json")["species_added"]})
    reg3 = load(RES / "tortoise_species_registry_v3.json")
    names.update({t["tortoise_key"]: t["scientific_name"] for t in reg3["species_added"]})
    groups = {g["tortoise_key"]: g for g in reg3["groups_not_species_specific"]}
    groups.update({k: {"tortoise_key": k, **g} for k, g in tr["tortoise_groups"].items()})

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

    sources, evidence = [], []
    for sid, s in tr["sources"].items():
        status = STATUS_BY_SOURCE_TYPE[s["source_type"]]
        sources.append({"source_id": sid, **{k: s[k] for k in ("citation", "url", "doi", "year", "language", "study_country", "publisher_country", "source_type",
                                                             "evidence_class", "method", "access", "what_was_read")}, "plant_record_count": len(s["records"]), "verification_status": status})
        for i, row in enumerate(s["records"], 1):
            r = dict(zip(v1.COLUMNS, row))
            methods, queried = row[12], (row[13] if len(row) > 13 else None)
            n = dict(v1.resolve(queried or r["plant_as_printed"], cache, a.offline))
            if n["name_check"] == "not_resolved_needs_review":
                alts = v2.homonyms(re.sub(r" (sp|spp)\.$", "", queried or r["plant_as_printed"]), cache, a.offline, load, dump)
                if alts and len(alts) > 1:
                    n.update(name_check="homonyms_in_backbone_author_not_given_needs_review", backbone_homonyms=alts)
            if re.search(COMMON, r["note"] or ""):
                n.update(accepted_name=None, family=None, name_check="common_name_only_not_resolved", rank_named_by_source="common_name_only", backbone_homonyms=None)
            typ = r["evidence_type"]
            cls = {8: "institutional_husbandry_guideline", 9: "keeper_organisation_statement"}.get(typ, "wild_feeding_study")
            direct = "statement_of_the_source_read" if typ in (8, 9) else "primary_study_read"
            sig = r["consumption_signal"]
            neg = ("not_eaten_in_study" if methods == ["not_detected_by_any_method"] else "source_advises_against" if re.search(r"advises against", sig) else
                   "animal_avoided_or_refused" if re.search(r"avoid|reject|refus", sig) else None)
            grp = groups.get(r["tortoise_key"])
            fam = re.match(r"family ([A-Z][a-z]+ceae)", r["note"] or "")
            e = {"evidence_id": "%s-%03d" % (sid, i), "unit": 4, "source_id": sid, "source_url": s["url"], "source_citation": s["citation"], "source_language": s["language"], "source_page": r["page"],
                 "tortoise_key": r["tortoise_key"], "tortoise_scientific_name": grp["label"] if grp else names[r["tortoise_key"]], "species_specific": not grp,
                 "plant_name_as_printed": r["plant_as_printed"], "plant_name_queried": queried or r["plant_as_printed"], "plant_accepted_name": n["accepted_name"], "plant_family": n.get("family"),
                 "plant_family_printed_by_source": fam.group(1) if fam else None, "plant_name_check": n["name_check"], "plant_rank_named_by_source": n["rank_named_by_source"],
                 "backbone_homonyms": n.get("backbone_homonyms"), "plant_part": r["plant_part"], "preparation_state": r["offered_form"], "wild_or_captive": r["wild_or_captive"],
                 "locality": r["locality"], "observed_consumption": sig, "quantity_as_reported": r["quantity_as_reported"], "study_method": s["method"], "detection_methods": methods,
                 "evidence_class": cls, "evidence_type": EVIDENCE_TYPES[typ], "evidence_directness": direct, "primary_reference_cited_by_source": r["primary_reference_cited_by_source"],
                 "is_negative_record": bool(neg), "negative_kind": neg, "applies_to_other_tortoise_species": "not established by this source",
                 "limitations": LIMIT + ("" if not grp else " The source does not tie this record to a single tortoise species.") + (" " + r["note"][0].upper() + r["note"][1:] + "." if r["note"] else ""),
                 "verification_status": status, "feeding_grade": None}
            e["evidence_tier"] = v3.tier_of(e)
            evidence.append(e)

    hazards = []
    for i, h in enumerate(tr["hazard_statements"], 1):
        ids = [e["evidence_id"] for e in evidence if e["source_id"] == h["source_id"] and e["plant_name_as_printed"] in h["applies_to_records_named"]]
        hazards.append({"hazard_id": "hz4-%02d" % i, **h, "evidence_ids": ids, "tested_in_tortoises_by_this_source": False,
                        "what_it_does_not_establish": "It does not show that the plant harms tortoises: the same source records leopard tortoises eating it and reports no health outcome. It also does not show that the plant is safe, and it gives no measured oxalate or toxin content."})
    hz_by_ev = {}
    for h in hazards + load(RES / "plant_hazard_statements_v3.json")["statements"]:
        for i in h["evidence_ids"]:
            hz_by_ev.setdefault(i, []).append(h["hazard_id"])

    # one index over units 1-4
    resolved = {r["name_as_printed"]: r["resolved_name"] for r in res3 if r["resolved_name"]}
    ledger = {r["v1_evidence_id"]: r["status_after_unit_3"] for r in ledger3}
    by_source = tr["method_by_source_for_units_1_to_3"]
    index = []
    for unit, recs in enumerate(old + [evidence], 1):
        for e in recs:
            acc = e["plant_accepted_name"] or resolved.get(e["plant_name_as_printed"])
            methods = e.get("detection_methods") or (methods_for(e) if e["source_id"] == "moorhouse_gann_2022" else [method_category(e, by_source)])
            index.append({"evidence_id": e["evidence_id"], "unit": unit, "source_id": e["source_id"], "tortoise_key": e["tortoise_key"], "tortoise": e["tortoise_scientific_name"],
                          "species_specific": e.get("species_specific", True), "plant_name_as_printed": e["plant_name_as_printed"], "plant_accepted_name": acc,
                          "name_from": "unit_record" if e["plant_accepted_name"] else "unit_3_name_resolution" if acc else None, "plant_name_check": e["plant_name_check"],
                          "plant_part": e["plant_part"], "preparation_state": e["preparation_state"], "wild_or_captive": e["wild_or_captive"],
                          "evidence_tier": e.get("evidence_tier") or v3.tier_of(e), "detection_methods": methods,
                          "detection_method_recorded_per_record": bool(e.get("detection_methods")), "evidence_directness": e["evidence_directness"],
                          "is_negative_record": e["is_negative_record"], "negative_kind": e.get("negative_kind") or ("animal_avoided_or_refused" if e["is_negative_record"] else None),
                          "quantity_as_reported": quantity_now(e),
                          "quantity_correction": ({"corrected_in_unit": 3, "action": corr3[e["evidence_id"]]["action"], "quantity_in_unit_record": e.get("quantity_as_reported"), "quantity_before_correction": corr3[e["evidence_id"]]["quantity_in_v2"],
                                                   "reason": corr3[e["evidence_id"]]["reason"]} if e["evidence_id"] in corr3 else None),
                          "unit_1_citation_status": ledger.get(e["evidence_id"]), "on_hold": e["evidence_id"] in held3, "hazard_statement_ids": sorted(hz_by_ev.get(e["evidence_id"], []))})
    live = [x for x in index if not x["on_hold"]]

    # duplicates and conflicts across units
    dup = {}
    for x in index:
        dup.setdefault((x["source_id"], x["tortoise_key"], x["plant_name_as_printed"], x["plant_part"], x["preparation_state"], x["wild_or_captive"], tuple(x["detection_methods"])), []).append(x["evidence_id"])
    same_record_groups = []
    by_full = {}
    full = {e["evidence_id"]: e for recs in old + [evidence] for e in recs}
    for x in index:
        e = full[x["evidence_id"]]
        by_full.setdefault((x["source_id"], x["tortoise_key"], x["plant_name_as_printed"], x["plant_part"], x["preparation_state"], x["wild_or_captive"], e["locality"]), []).append(x["evidence_id"])
    same_record_groups = [ids for ids in by_full.values() if len(ids) > 1]
    pairs = {}
    for x in live:
        if x["plant_accepted_name"]:
            pairs.setdefault((x["tortoise_key"], x["plant_accepted_name"]), []).append(x)
    conflicts = []
    for (tk, plant), xs in sorted(pairs.items()):
        neg, pos = [x for x in xs if x["is_negative_record"]], [x for x in xs if not x["is_negative_record"]]
        if neg and pos:
            conflicts.append({"tortoise_key": tk, "plant_accepted_name": plant, "records_eaten": [x["evidence_id"] for x in pos], "records_not_eaten_or_avoided": [x["evidence_id"] for x in neg],
                              "negative_kinds": sorted({x["negative_kind"] for x in neg}), "note": "Both kinds of record are kept. Neither is deleted or averaged."})
    corroborated = sum(1 for xs in pairs.values() if len({x["source_id"] for x in xs if x["evidence_directness"] == "primary_study_read" and not x["is_negative_record"]}) > 1)

    # cumulative candidates
    cands = {c["candidate_key"]: {**{k: (list(v) if isinstance(v, list) else v) for k, v in c.items()}} for c in cand3}
    for e in evidence:
        acc = e["plant_accepted_name"] or resolved.get(e["plant_name_as_printed"])
        key = acc or "printed:" + e["plant_name_as_printed"]
        c = cands.setdefault(key, {"candidate_key": key, "accepted_name": acc, "family": e["plant_family"], "rank": e["plant_rank_named_by_source"] if e["plant_accepted_name"] else ("species" if acc and " " in acc else e["plant_rank_named_by_source"]),
                                   "names_as_printed": [], "name_check": e["plant_name_check"], "evidence_ids": [], "seed_mixture_ids": [], "forage_nutrition_record_ids": [],
                                   "existing_plant_ids": [], "existing_genus_level_plant_ids": [], "first_seen_in_unit": 4, "feeding_grade": None})
        if e["plant_name_as_printed"] not in c["names_as_printed"]:
            c["names_as_printed"].append(e["plant_name_as_printed"])
        c["evidence_ids"].append(e["evidence_id"])
    ix = {x["evidence_id"]: x for x in index}
    for c in cands.values():
        xs = [ix[i] for i in c["evidence_ids"]]
        lv = [x for x in xs if not x["on_hold"]]
        c["evidence_ids_on_hold"] = sorted(x["evidence_id"] for x in xs if x["on_hold"])
        c["tortoise_taxa_with_records"] = sorted({x["tortoise"] for x in lv})
        c["negative_record_only"] = all(x["is_negative_record"] for x in lv) if lv else None
        c["evidence_by_tier"] = dict(sorted(Counter(x["evidence_tier"] for x in lv).items()))
        c["evidence_by_detection_method"] = dict(sorted(Counter(m for x in lv for m in x["detection_methods"]).items()))
        scope = {}
        for x in lv:
            s = scope.setdefault(x["tortoise_key"], {"tortoise_key": x["tortoise_key"], "tortoise": x["tortoise"], "species_specific": x["species_specific"], "tiers": [], "parts": [], "detection_methods": [],
                                                    "eaten_records": 0, "not_eaten_or_avoided_records": 0})
            for k, v in (("tiers", [x["evidence_tier"]]), ("parts", [x["plant_part"]]), ("detection_methods", x["detection_methods"])):
                s[k] += [y for y in v if y not in s[k]]
            s["not_eaten_or_avoided_records" if x["is_negative_record"] else "eaten_records"] += 1
        c["tortoise_scope"] = sorted(scope.values(), key=lambda s: s["tortoise_key"])
        c["best_evidence_tier"] = min(c["evidence_by_tier"]) if c["evidence_by_tier"] else None
        c["hazard_statement_ids"] = sorted({h for x in xs for h in x["hazard_statement_ids"]})
        acc = c["accepted_name"]
        if acc and c["rank"] == "species":
            c["existing_plant_ids"] = sorted(by_species.get(acc, []))
            c["existing_genus_level_plant_ids"] = sorted(by_genus.get(acc.split()[0], []))
        elif acc and c["rank"] == "genus":
            c["existing_genus_level_plant_ids"] = sorted(by_genus.get(acc, []))
        c["database_status"] = ("species_already_in_database" if c["existing_plant_ids"] else "genus_level_record_in_database" if c["existing_genus_level_plant_ids"] else
                                "not_in_database" if c["rank"] in ("species", "genus") and acc else "unresolved_name_not_a_candidate")
        c["generalisation_note"] = "Evidence is listed per tortoise taxon. A record for one tortoise taxon is not evidence for another."

    # review queue
    names_review = {}
    for x in index:
        if not x["plant_accepted_name"] and x["plant_name_check"] != "common_name_only_not_resolved" and x["plant_name_check"] not in ("accepted",):
            names_review.setdefault(x["plant_name_as_printed"], {"name_as_printed": x["plant_name_as_printed"], "name_check": x["plant_name_check"], "evidence_ids": []})["evidence_ids"].append(x["evidence_id"])
    fam_diff = [{"evidence_id": e["evidence_id"], "plant_name_as_printed": e["plant_name_as_printed"], "family_printed": e["plant_family_printed_by_source"], "family_in_backbone": e["plant_family"]}
                for e in evidence if e["plant_family_printed_by_source"] and e["plant_family"] and e["plant_family_printed_by_source"] != e["plant_family"]]
    genus_fams = {}
    for x in index:
        fam = full[x["evidence_id"]].get("plant_family")
        if x["plant_accepted_name"] and fam and x["name_from"] == "unit_record":
            genus_fams.setdefault(x["plant_accepted_name"].split()[0], set()).add(fam)
    queue = {
        "genus_with_more_than_one_backbone_family": [{"genus": g, "families": sorted(f)} for g, f in sorted(genus_fams.items()) if len(f) > 1],
        "unit_1_citations_not_read": [{"v1_evidence_id": r["v1_evidence_id"], "cited": r["primary_reference_cited_by_source"], "search_status": r.get("cited_primary_search_status")}
                                      for r in ledger3 if r["status_after_unit_3"] == "secondary_citation_primary_not_read"],
        "unit_1_citations_not_supported_by_the_cited_source": [r["v1_evidence_id"] for r in ledger3 if r["status_after_unit_3"].startswith("cited_source_read") or r["status_after_unit_3"].startswith("not_in_the_cited")],
        "names_needing_review": sorted(names_review.values(), key=lambda n: n["name_as_printed"]),
        "family_printed_differs_from_backbone_unit_4": fam_diff,
        "conflicting_records_same_tortoise_and_plant": conflicts,
        "records_on_hold": [{"evidence_id": i, "reason": c["reason"]} for i, c in held3.items()],
        "identical_record_groups_across_units": same_record_groups,
        "duplicate_datasets_not_added": tr["duplicate_datasets"],
        "sources_on_hold_unit_4": tr["sources_on_hold"],
    }

    def cc(cs):
        new = [c for c in cs if c["database_status"] == "not_in_database"]
        return {"plant_names": len(cs), "new_candidates_not_in_database": len(new), "new_candidates_species_level": sum(c["rank"] == "species" for c in new),
                "new_candidates_genus_level": sum(c["rank"] == "genus" for c in new), "species_already_in_database": sum(c["database_status"] == "species_already_in_database" for c in cs),
                "genus_level_record_in_database": sum(c["database_status"] == "genus_level_record_in_database" for c in cs),
                "unresolved_not_a_candidate": sum(c["database_status"] == "unresolved_name_not_a_candidate" for c in cs)}

    per = {}
    for x in live:
        t = per.setdefault(x["tortoise"], {"records": 0, "added_in_unit_4": 0, "species_specific": x["species_specific"], "by_detection_method": Counter(), "by_tier": Counter()})
        t["records"] += 1
        t["added_in_unit_4"] += x["unit"] == 4
        t["by_tier"][x["evidence_tier"]] += 1
        for m in x["detection_methods"]:
            t["by_detection_method"][m] += 1
    for t in per.values():
        t["by_tier"], t["by_detection_method"] = dict(sorted(t["by_tier"].items())), dict(sorted(t["by_detection_method"].items()))
    summary = {
        "unit_4_added": {"sources_read": len(sources), "sources_by_type": dict(sorted(Counter(s["source_type"] for s in sources).items())), "evidence_records": len(evidence),
                         "evidence_species_specific": sum(e["species_specific"] for e in evidence), "evidence_by_tier": dict(sorted(Counter(e["evidence_tier"] for e in evidence).items())),
                         "evidence_by_detection_method": dict(sorted(Counter(m for e in evidence for m in e["detection_methods"]).items())),
                         "negative_records_by_kind": dict(sorted(Counter(e["negative_kind"] for e in evidence if e["negative_kind"]).items())),
                         "plant_part_stated": sum(e["plant_part"] != "not stated" for e in evidence), "plant_part_not_stated": sum(e["plant_part"] == "not stated" for e in evidence),
                         "plant_names_by_check": dict(sorted(Counter(n for n in {e["plant_name_as_printed"]: e["plant_name_check"] for e in evidence}.values()).items())),
                         "hazard_statements": len(hazards), "duplicate_datasets_not_added": len(tr["duplicate_datasets"])},
        "cumulative": {"evidence_records": len(index), "evidence_records_on_hold": len(index) - len(live), "evidence_by_tier": dict(sorted(Counter(x["evidence_tier"] for x in live).items())),
                       "evidence_by_detection_method": dict(sorted(Counter(m for x in live for m in x["detection_methods"]).items())),
                       "candidates": cc(list(cands.values())), "candidates_in_unit_3": cc(cand3),
                       "tortoise_plant_pairs_with_two_or_more_independent_primary_sources": corroborated},
        "per_tortoise": dict(sorted(per.items())),
        "review_queue": {k: len(v) for k, v in queue.items()},
        "gaps_not_filled": tr["gaps_not_filled"],
    }
    meta = {"schema_version": "4.0", "generated_by": "scripts/build_global_plant_evidence_research_v4.py", "generated_from": "data/research/global_plant_evidence_transcription_v4.json",
            "extends": "the v1, v2 and v3 research files, which are not modified", "layer": "research_only_not_published", "grade_policy": v1.GRADE_POLICY}
    dump(RES / "global_evidence_sources_v4.json", {**meta, "sources": sources, "duplicate_datasets": tr["duplicate_datasets"], "on_hold": tr["sources_on_hold"]})
    dump(RES / "tortoise_species_registry_v4.json", {**meta, "species_added": [], "groups_not_species_specific": [{"tortoise_key": k, **g} for k, g in tr["tortoise_groups"].items()]})
    dump(RES / "tortoise_plant_evidence_v4.json", {**meta, "records": evidence})
    dump(RES / "plant_hazard_statements_v4.json", {**meta, "note": "Statements made by sources that were read. They are not toxicity findings for tortoises.", "statements": hazards})
    dump(RES / "evidence_index_v4.json", {**meta, "note": "For units 1-3 the detection method was not recorded per record; it is derived here from the record and from a per-source table in the unit-4 transcription, and 'detection_method_recorded_per_record' is false. For Moorhouse-Gann 2022 the methods are read from each record's quantity text after the unit-3 corrections. 'quantity_as_reported' is the value after those corrections; a held record has none.", "records": index})
    dump(RES / "plant_candidates_v4.json", {**meta, "scope": "cumulative over units 1 to 4", "candidates": sorted(cands.values(), key=lambda c: c["candidate_key"])})
    dump(RES / "review_queue_v4.json", {**meta, "queue": queue})
    dump(RES / "research_layer_summary_v4.json", {**meta, "summary": summary})
    print("unit 4: sources %d, evidence %d, cumulative %d, candidates %d, hazards %d, conflicts %d, names for review %d"
          % (len(sources), len(evidence), len(index), len(cands), len(hazards), len(conflicts), len(names_review)))


if __name__ == "__main__":
    main()
