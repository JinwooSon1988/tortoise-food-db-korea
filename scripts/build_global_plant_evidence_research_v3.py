#!/usr/bin/env python3
"""Build the unit-3 research data sets from data/research/global_plant_evidence_transcription_v3.json.

Unit 3 only adds files. The v1 and v2 research files are read and never rewritten.

Writes, in data/research:
  global_evidence_sources_v3.json      sources read in unit 3, the status of every publication cited by unit-1 records, holds
  tortoise_species_registry_v3.json    tortoise taxon added in unit 3 and the non-specific groups used by some sources
  tortoise_plant_evidence_v3.json      evidence records added in unit 3, each with an evidence tier and a species-specific flag
  primary_verification_ledger_v3.json  one row per unit-1 evidence record with its status after unit 3
  record_corrections_v3.json           corrections to unit-2 records (the v2 file itself is not edited)
  plant_name_resolutions_v3.json       names left for review in units 1-3, checked against a second database (World Flora Online)
  plant_candidates_v3.json             cumulative candidate list with evidence tiers and tortoise scope per plant
  plant_hazard_statements_v3.json      toxicity and antinutrient statements made by the sources that were read
  nutrient_safety_view_v3.json         calcium, phosphorus, fibre and protein values already held, laid out per record
  research_layer_summary_v3.json       counts

Usage:
  python scripts/build_global_plant_evidence_research_v3.py --cache <GBIF cache dir> --wfo-cache <WFO cache dir> [--offline]

No feeding grade is assigned anywhere.
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
STATUS_BY_SOURCE_TYPE = {
    "peer_reviewed_field_study": "verified_primary_source", "peer_reviewed_monograph": "verified_primary_source",
    "society_journal_field_study": "verified_primary_source_society_journal", "university_repository_paper": "verified_primary_source_repository_paper",
    "government_technical_report": "verified_document_no_feeding_content", "zoo_association_husbandry_guideline": "verified_husbandry_guideline",
    "museum_veterinary_husbandry_guideline": "verified_husbandry_guideline", "keeper_organisation_web_page": "verified_keeper_organisation_page"}
STUDY_TYPES = ("peer_reviewed_field_study", "peer_reviewed_monograph", "society_journal_field_study", "university_repository_paper")
EVIDENCE_TYPES = {1: "direct_study_of_this_tortoise_species", 5: "husbandry_note_in_a_publication", 8: "institutional_husbandry_guideline", 9: "keeper_organisation_statement"}
TIER_KO = {"1_wild_feeding_study_read": "야생 섭식 연구(원문 열람)", "2_semi_wild_feeding_study_read": "자연 식생 울타리 안 연구(원문 열람)",
           "3_captive_feeding_trial_read": "사육 급여 시험(원문 열람)", "4_institutional_husbandry_guideline": "동물원·수의 사육 지침",
           "5_husbandry_practice_reported": "문헌에 실린 사육 급여 관행", "6_keeper_organisation_statement": "전문 사육단체 자료",
           "7_local_or_community_report": "현지·주민 보고", "8_secondary_citation_primary_not_read": "2차 인용(1차 문헌 미열람)",
           "9_review_or_account_statement": "종 계정·보전계획의 서술"}
LIMIT = "Records what this tortoise taxon was reported to eat or be fed. It does not establish safe amounts, long-term outcomes or suitability for other tortoise species."
REVIEW_STATES = ("spelling_differs_from_backbone_needs_review", "homonyms_in_backbone_author_not_given_needs_review", "not_resolved_needs_review",
                 "backbone_match_conflicts_with_source_needs_review", "synonym_in_backbone_but_source_lists_both_names_kept_separate")


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    argv, sys.argv = sys.argv, ["x"]
    spec.loader.exec_module(m)
    sys.argv = argv
    return m


def tier_of(e):
    cls, direct, typ = e.get("evidence_class"), e["evidence_directness"], e["evidence_type"]
    if direct in ("reported_in_account_primary_not_read", "reported_in_source_primary_not_read"):
        return "8_secondary_citation_primary_not_read"
    if cls == "institutional_husbandry_guideline":
        return "4_institutional_husbandry_guideline"
    if cls == "keeper_organisation_statement":
        return "6_keeper_organisation_statement"
    if cls in ("local_knowledge", "community_provisioning") or typ == "local_knowledge_report":
        return "7_local_or_community_report"
    if cls == "husbandry_practice" or typ in ("specialist_husbandry_practice", "husbandry_note_in_a_publication"):
        return "5_husbandry_practice_reported"
    if cls == "captive_feeding_trial":
        return "3_captive_feeding_trial_read"
    if cls == "semi_wild_feeding_study":
        return "2_semi_wild_feeding_study_read"
    if cls == "field_observation_of_previously_captive_tortoise":
        return "2b_previously_captive_animal_field_observation_read"
    if direct == "primary_study_read":
        return "1_wild_feeding_study_read"
    return "9_review_or_account_statement"


def lev(a, b):
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def placement(p):
    """Accepted taxon and family from a World Flora Online placement path ('.../Family/.../Genus/epithet$Name/parts')."""
    if not p or "$" not in p:
        return None, None
    segs = p.split("$")[0].split("/")
    fam = next((s for s in segs if s.endswith("aceae")), None)
    gi = max((i for i, s in enumerate(segs) if s[:1].isupper()), default=None)
    if gi is None:
        return None, fam
    return (segs[gi] + (" " + segs[gi + 1] if gi + 1 < len(segs) else "")), fam


def canon(full):
    w = full.split()
    return " ".join(w[:2]) if len(w) > 1 and w[1][:1].islower() else w[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True)
    ap.add_argument("--wfo-cache", required=True)
    ap.add_argument("--offline", action="store_true")
    a = ap.parse_args()
    cache, wcache = Path(a.cache), Path(a.wfo_cache)
    wcache.mkdir(parents=True, exist_ok=True)
    v1 = module(ROOT / "scripts/build_global_plant_evidence_research_v1.py", "build_v1")
    v2 = module(ROOT / "scripts/build_global_plant_evidence_research_v2.py", "build_v2")
    load, dump = v1.load, v1.dump
    tr = load(RES / "global_plant_evidence_transcription_v3.json")
    ev1 = load(RES / "tortoise_plant_evidence_v1.json")["records"]
    ev2 = load(RES / "tortoise_plant_evidence_v2.json")["records"]
    cand2 = load(RES / "plant_candidates_v2.json")["candidates"]
    ledger2 = load(RES / "primary_verification_ledger_v2.json")["records"]
    nut = load(RES / "forage_nutrition_research_v1.json")["records"] + load(RES / "forage_nutrition_research_v2.json")["records"]
    plants = load(ROOT / "data/plants.json")

    def wfo(query):
        f = wcache / (re.sub(r"[^A-Za-z0-9]+", "_", query).strip("_") + ".json")
        if f.exists():
            return load(f)
        if a.offline:
            return None
        url = "https://list.worldfloraonline.org/matching_rest.php?" + urllib.parse.urlencode({"input_string": query})
        d = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "tortoise-food-db-korea research"}), timeout=60))
        slim = {"classification_version": d.get("params", {}).get("classificationVersion"),
                "match": d.get("match") and {"full_name": d["match"]["full_name_plain"], "wfo_id": d["match"]["wfo_id"], "placement": d["match"].get("placement")},
                "candidates": [{"full_name": c["full_name_plain"], "wfo_id": c["wfo_id"], "placement": c.get("placement")} for c in (d.get("candidates") or [])[:12]]}
        dump(f, slim)
        time.sleep(0.5)
        return slim

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

    # tortoise registry
    names = {t["tortoise_key"]: t["scientific_name"] for t in load(RES / "tortoise_species_registry_v1.json")["species"]}
    names.update({t["tortoise_key"]: t["scientific_name"] for t in load(RES / "tortoise_species_registry_v2.json")["species_added"]})
    registry = []
    for key, t in tr["tortoises_added"].items():
        d = v1.gbif(t["scientific_name"], "Animalia", cache, a.offline) or {}
        names[key] = t["scientific_name"]
        registry.append({"tortoise_key": key, **t, "gbif_match_type": d.get("matchType"), "gbif_status": d.get("status"), "gbif_usage_key": d.get("usageKey"),
                         "gbif_accepted_name": d.get("species"), "family": d.get("family"),
                         "name_check": "accepted" if d.get("matchType") == "EXACT" and d.get("status") == "ACCEPTED" else "needs_review"})
    groups = tr["tortoise_groups"]
    for key, g in groups.items():
        for mk in g["member_tortoise_keys"]:
            if mk not in names:
                raise SystemExit("group %s: unknown member %s" % (key, mk))

    resolved = {}

    def res(printed, queried=None):
        k = (printed, queried)
        if k not in resolved:
            r = v1.resolve(queried or printed, cache, a.offline)
            r["name_queried"] = queried or printed
            if r["name_check"] == "not_resolved_needs_review":
                alts = v2.homonyms(re.sub(r" (sp|spp)\.$", "", queried or printed), cache, a.offline, load, dump)
                if alts and len(alts) > 1:
                    r["name_check"], r["backbone_homonyms"] = "homonyms_in_backbone_author_not_given_needs_review", alts
            resolved[k] = r
        return resolved[k]

    sources, evidence = [], []
    for sid, s in tr["sources"].items():
        status = STATUS_BY_SOURCE_TYPE[s["source_type"]]
        sources.append({"source_id": sid, **{k: s[k] for k in ("citation", "url", "doi", "year", "language", "study_country", "publisher_country", "source_type",
                                                             "evidence_class", "method", "access", "what_was_read")},
                        "plant_record_count": len(s["records"]), "verification_status": status, **({"rows_not_transcribed": s["rows_not_transcribed"]} if "rows_not_transcribed" in s else {})})
        for i, row in enumerate(s["records"], 1):
            r = dict(zip(v1.COLUMNS, row))
            n = dict(res(r["plant_as_printed"], row[12] if len(row) > 12 else None))
            if re.search(r"common names? only|common name as printed|local name only|food group only|plant group only|unidentified|not identified", r["note"] or ""):
                # the transcription says the source gives no scientific name: never send such a label to a name database
                n.update(accepted_name=None, family=None, name_check="common_name_only_not_resolved", rank_named_by_source="common_name_only", backbone_homonyms=None)
            typ = r["evidence_type"]
            cls = {8: "institutional_husbandry_guideline", 9: "keeper_organisation_statement", 5: "husbandry_practice"}.get(typ, "wild_feeding_study")
            direct = ("statement_of_the_source_read" if typ in (8, 9) else "husbandry_note_in_primary_source_read" if typ == 5 else
                      "primary_study_read" if s["source_type"] in STUDY_TYPES else "statement_of_the_source_read")
            sig = r["consumption_signal"]
            neg = ("source_advises_against" if re.search(r"advises against", sig) else "animal_avoided_or_refused" if re.search(r"avoid|reject|refus", sig) else None)
            grp = groups.get(r["tortoise_key"])
            e = {"evidence_id": "%s-%02d" % (sid, i), "unit": 3, "source_id": sid, "source_url": s["url"], "source_citation": s["citation"], "source_language": s["language"], "source_page": r["page"],
                 "tortoise_key": r["tortoise_key"], "tortoise_scientific_name": grp["label"] if grp else names[r["tortoise_key"]],
                 "species_specific": not grp, "tortoise_species_named_by_source": grp["species_named_by_source"] if grp else True,
                 "plant_name_as_printed": r["plant_as_printed"], "plant_name_queried": n["name_queried"], "plant_accepted_name": n["accepted_name"], "plant_family": n.get("family"),
                 "plant_name_check": n["name_check"], "plant_rank_named_by_source": n["rank_named_by_source"], "backbone_homonyms": n.get("backbone_homonyms"),
                 "plant_part": r["plant_part"], "preparation_state": r["offered_form"], "wild_or_captive": r["wild_or_captive"], "locality": r["locality"],
                 "observed_consumption": sig, "quantity_as_reported": r["quantity_as_reported"], "study_method": s["method"],
                 "evidence_class": cls, "evidence_type": EVIDENCE_TYPES[typ], "evidence_directness": direct, "primary_reference_cited_by_source": r["primary_reference_cited_by_source"],
                 "is_negative_record": bool(neg), "negative_kind": neg, "applies_to_other_tortoise_species": "not established by this source",
                 "limitations": LIMIT + ("" if not grp else " The source does not tie this record to a single tortoise species.") + (" " + r["note"][0].upper() + r["note"][1:] + "." if r["note"] else ""),
                 "verification_status": status, "feeding_grade": None}
            e["evidence_tier"] = tier_of(e)
            e["evidence_tier_ko"] = TIER_KO[e["evidence_tier"]]
            evidence.append(e)
    all_ev = ev1 + ev2 + evidence
    by_id = {e["evidence_id"]: e for e in all_ev}

    # ledger after unit 3
    upd = {x["v1_evidence_id"]: x for x in tr["primary_verification_of_v1_records"]}
    v3_by_plant = {(e["source_id"], e["plant_name_as_printed"]): e["evidence_id"] for e in evidence}
    cited = {x["cited_as"]: x for x in tr["cited_primary_status"]}
    ledger = []
    for r in ledger2:
        row = {k: r[k] for k in ("v1_evidence_id", "tortoise_scientific_name", "plant_name_as_printed", "directness_in_unit_1", "primary_reference_cited_by_source")}
        row.update(status_after_unit_2=r["status_after_unit_2"], status_after_unit_3=r["status_after_unit_2"], primary_source_id=r.get("primary_source_id"),
                   confirming_evidence_id=r.get("v2_evidence_id"), checked_in_unit=None, note=r.get("note"))
        if r["status_after_unit_2"].startswith("confirmed") or r["status_after_unit_2"].startswith("not_in_the_cited"):
            row["checked_in_unit"] = 2
        elif r["status_after_unit_2"] == "primary_read_in_unit_1":
            row["checked_in_unit"] = 1
        if r["v1_evidence_id"] in upd:
            u = upd[r["v1_evidence_id"]]
            row.update(status_after_unit_3=u["result"], primary_source_id=u["primary_source_id"], checked_in_unit=3, note=u["note"],
                       confirming_evidence_id=v3_by_plant.get((u["primary_source_id"], u["v3_record_plant"])) if u["v3_record_plant"] else None)
        if row["status_after_unit_3"] == "secondary_citation_primary_not_read":
            c = cited.get(r["primary_reference_cited_by_source"], {})
            row["cited_primary_search_status"], row["note"] = c.get("status", "not_listed"), c.get("note")
        e1 = by_id[r["v1_evidence_id"]]
        row["independent_primary_records_same_tortoise_and_plant"] = sorted(
            p["evidence_id"] for p in all_ev if p["evidence_directness"] == "primary_study_read" and e1["plant_accepted_name"] and p["plant_accepted_name"] == e1["plant_accepted_name"]
            and p["tortoise_key"] == e1["tortoise_key"] and p["source_id"] != e1["source_id"] and p["evidence_id"] != row["confirming_evidence_id"])
        ledger.append(row)

    # corrections to unit-2 records
    corrections = []
    # the quantity before correction comes from the unit-2 transcription, so it survives later edits of the unit-2 evidence file
    tr2 = load(RES / "global_plant_evidence_transcription_v2.json")
    tr2_quantity = {"%s-%02d" % (sid, i): row[6] for sid, s2 in tr2["sources"].items() for i, row in enumerate(s2["records"], 1)}
    for c in tr["record_corrections_to_v2"]:
        target = [e for e in ev2 if e["source_id"] == c["v2_source_id"] and e["plant_name_as_printed"] == c["v2_evidence_plant"]]
        if len(target) != 1:
            raise SystemExit("correction target not unique: %s" % c["v2_evidence_plant"])
        corrections.append({"evidence_id": target[0]["evidence_id"], "plant_name_as_printed": c["v2_evidence_plant"], "action": c["action"], "reason": c["reason"],
                            "quantity_in_v2": tr2_quantity.get(target[0]["evidence_id"], target[0]["quantity_as_reported"]), "corrected_quantity": c["corrected_quantity"],
                            "status_after_correction": "hold_table_cell_not_determinable" if c["action"] == "put_on_hold" else "kept_without_quantity"})
    on_hold_ids = {c["evidence_id"] for c in corrections if c["action"] == "put_on_hold"}

    # second-database check of names left for review
    hints = {h["name"]: h for h in tr["name_hints"]}
    review = {}
    for e in all_ev:
        if e["plant_name_check"] in REVIEW_STATES:
            review.setdefault(e["plant_name_as_printed"], {"previous_name_check": e["plant_name_check"], "queried": e.get("plant_name_queried") or e["plant_name_as_printed"], "evidence_ids": []})["evidence_ids"].append(e["evidence_id"])
    resolutions = []
    for printed in sorted(review):
        rv = review[printed]
        q = re.sub(r" (sp|spp)\.$", "", rv["queried"])
        h = hints.get(printed)
        out = {"name_as_printed": printed, "previous_name_check": rv["previous_name_check"], "decision": "still_unresolved", "resolved_name": None, "resolved_family": None,
               "second_database": "World Flora Online plant list, name matching service", "second_database_result": None, "gbif_result": None, "reason": None,
               "applies_to_evidence_ids": rv["evidence_ids"]}
        g = v1.resolve(rv["queried"], cache, a.offline)
        out["gbif_result"] = {"name_check": g["name_check"], "fuzzy_candidate": g.get("gbif_fuzzy_candidate")}
        if h and h["kind"] == "resolved_by_source_context":
            w, gg = wfo(h["intended_name"]), v1.gbif(h["intended_name"], "Plantae", cache, a.offline)
            if w and w["match"] and gg and gg.get("matchType") == "EXACT":
                acc_w, fam = placement(w["match"]["placement"])
                out.update(decision="resolved_by_source_context", resolved_name=gg.get("species") if gg.get("status") == "ACCEPTED" else None, resolved_family=gg.get("family"),
                           second_database_result={"matched": w["match"]["full_name"], "accepted_in_wfo": acc_w, "family": fam},
                           intended_name=h["intended_name"], reason=h["reason"] + (" GBIF accepts %s; World Flora Online places it under %s. The two databases disagree on the genus, so the GBIF name is used for linking and both are recorded." % (gg.get("species"), acc_w) if acc_w != gg.get("species") else ""))
        elif h and h["kind"] == "author_printed_in_source":
            w = wfo("%s %s" % (q, h["author"]))
            if w and w["match"]:
                acc_w, fam = placement(w["match"]["placement"])
                out.update(decision="resolved_homonym_by_author_printed_in_source", resolved_name=acc_w, resolved_family=fam,
                           second_database_result={"matched": w["match"]["full_name"], "accepted_in_wfo": acc_w, "family": fam}, reason=h["reason"])
        else:
            w = wfo(q)
            # a second-database result is adopted only when GBIF lists the same accepted species among its same-spelled names
            gb_alts = {x["accepted_species"] for x in (v2.homonyms(q, cache, a.offline, load, dump) or []) if x["accepted_species"]}
            if w:
                cands_w = ([w["match"]] if w["match"] else []) + w["candidates"]
                placed = [(c["full_name"], *placement(c["placement"])) for c in cands_w]
                out["second_database_result"] = {"single_match": bool(w["match"]), "names": [{"name": n, "accepted_in_wfo": acc, "family": fam} for n, acc, fam in placed[:8]]}
                if rv["previous_name_check"].startswith("spelling_differs"):
                    fz = g.get("gbif_fuzzy_candidate")
                    hit = [(n, acc, fam) for n, acc, fam in placed if fz and canon(n) == fz and acc]
                    gg = v1.gbif(fz, "Plantae", cache, a.offline) if fz else None
                    accs = {acc for _, acc, _ in hit}
                    if fz and hit and lev(q.lower(), fz.lower()) <= 2 and gg and gg.get("matchType") == "EXACT" and gg.get("species") in accs:
                        out.update(decision="resolved_orthographic_variant", resolved_name=gg["species"], resolved_family=gg.get("family"), corrected_spelling=fz,
                                   reason="The printed name differs from '%s' by %d letter(s); GBIF and World Flora Online both hold that name and give the same accepted species." % (fz, lev(q.lower(), fz.lower())))
                    elif fz and hit:
                        out.update(decision="spelling_variant_identified_accepted_name_not_agreed", corrected_spelling=fz,
                                   reason="A close spelling exists in both databases, but they do not give one and the same accepted species (or the difference is more than two letters).")
                elif w["match"]:
                    acc_w, fam = placement(w["match"]["placement"])
                    same = canon(w["match"]["full_name"]) == q
                    if rv["previous_name_check"].startswith("synonym_in_backbone_but_source"):
                        if same and acc_w == q:
                            out.update(decision="resolved_source_and_second_database_treat_as_distinct", resolved_name=acc_w, resolved_family=fam,
                                       reason="World Flora Online accepts the name as its own species, as the source does; GBIF treats it as a synonym.")
                    elif same and acc_w and acc_w in gb_alts:
                        out.update(decision="resolved_by_second_database", resolved_name=acc_w, resolved_family=fam,
                                   reason="GBIF could not choose among names spelled this way; World Flora Online has a single name, and its accepted species is one of those GBIF lists for this spelling.")
                elif len({acc for n, acc, _ in placed if acc and canon(n) == q}) == 1 and not rv["previous_name_check"].startswith("synonym_in_backbone_but_source")                         and next(acc for n, acc, _ in placed if acc and canon(n) == q) in gb_alts:
                    acc_w, fam = next((acc, fam) for n, acc, fam in placed if acc and canon(n) == q)
                    out.update(decision="resolved_by_second_database", resolved_name=acc_w, resolved_family=fam,
                               reason="GBIF could not choose among names spelled this way; in World Flora Online every name with this spelling that has a placement leads to the same accepted species, which GBIF also lists for this spelling.")
                elif len({acc for _, acc, _ in placed if acc}) > 1:
                    out["reason"] = "Several plant names are spelled this way and they belong to different accepted species; the source gives no author."
        resolutions.append(out)
    res_by_name = {r["name_as_printed"]: r for r in resolutions if r["resolved_name"]}

    # cumulative candidates with tiers and tortoise scope
    cands = {c["candidate_key"]: {**{k: (list(v) if isinstance(v, list) else v) for k, v in c.items()}} for c in cand2}

    def target(acc, fam, rank, check, printed):
        key = acc or "printed:" + printed
        c = cands.setdefault(key, {"candidate_key": key, "accepted_name": acc, "family": fam, "rank": rank, "names_as_printed": [], "name_check": check,
                                   "tortoise_taxa_with_records": [], "evidence_ids": [], "negative_record_only": None, "seed_mixture_ids": [], "existing_plant_ids": [],
                                   "existing_genus_level_plant_ids": [], "forage_nutrition_record_ids": [], "first_seen_in_unit": 3, "feeding_grade": None})
        if printed not in c["names_as_printed"]:
            c["names_as_printed"].append(printed)
        return c

    for e in evidence:
        c = target(e["plant_accepted_name"], e["plant_family"], e["plant_rank_named_by_source"], e["plant_name_check"], e["plant_name_as_printed"])
        c["evidence_ids"].append(e["evidence_id"])
    for printed, r in res_by_name.items():           # move resolved names under their accepted name
        old = cands.pop("printed:" + printed, None)
        if not old:
            continue
        c = target(r["resolved_name"], r["resolved_family"], old["rank"], "resolved_in_unit_3:" + r["decision"], printed)
        for k in ("evidence_ids", "seed_mixture_ids", "forage_nutrition_record_ids", "names_as_printed"):
            c[k] += [x for x in old[k] if x not in c[k]]
        c["first_seen_in_unit"] = min(c["first_seen_in_unit"], old["first_seen_in_unit"])
        c["rank"] = "species" if " " in r["resolved_name"] else "genus"
    hazards = []
    for i, h in enumerate(tr["hazard_statements"], 1):
        ids = [e["evidence_id"] for e in all_ev if e["source_id"] == h["source_id"] and e["plant_name_as_printed"] == h["plant_as_printed"] and e["tortoise_key"] == h["tortoise_key"]]
        hazards.append({"hazard_id": "hz3-%02d" % i, **h, "evidence_ids": ids, "tested_in_tortoises_by_this_source": False,
                        "what_it_does_not_establish": "It does not show that the plant harms tortoises: the same source records tortoises eating it, and it reports no feeding trial or health outcome. It also does not show that the plant is safe."})
    hz_by_ev = {}
    for h in hazards:
        for i in h["evidence_ids"]:
            hz_by_ev.setdefault(i, []).append(h["hazard_id"])
    for c in cands.values():
        evs = [by_id[i] for i in c["evidence_ids"]]
        live = [e for e in evs if e["evidence_id"] not in on_hold_ids]
        c["evidence_ids_on_hold"] = sorted(e["evidence_id"] for e in evs if e["evidence_id"] in on_hold_ids)
        c["tortoise_taxa_with_records"] = sorted({e["tortoise_scientific_name"] for e in live})
        c["negative_record_only"] = all(e["is_negative_record"] for e in live) if live else None
        c["evidence_by_tier"] = dict(sorted(Counter(e.get("evidence_tier") or tier_of(e) for e in live).items()))
        scope = {}
        for e in live:
            s = scope.setdefault(e["tortoise_key"], {"tortoise_key": e["tortoise_key"], "tortoise": e["tortoise_scientific_name"], "species_specific": e.get("species_specific", True), "tiers": [], "parts": []})
            t = e.get("evidence_tier") or tier_of(e)
            if t not in s["tiers"]:
                s["tiers"].append(t)
            if e["plant_part"] not in s["parts"]:
                s["parts"].append(e["plant_part"])
        c["tortoise_scope"] = sorted(scope.values(), key=lambda s: s["tortoise_key"])
        c["best_evidence_tier"] = min(c["evidence_by_tier"]) if c["evidence_by_tier"] else None
        c["hazard_statement_ids"] = sorted({h for e in evs for h in hz_by_ev.get(e["evidence_id"], [])})
        acc = c["accepted_name"]
        if acc and c["rank"] == "species":
            c["existing_plant_ids"] = sorted(by_species.get(acc, []))
            c["existing_genus_level_plant_ids"] = sorted(by_genus.get(acc.split()[0], []))
        elif acc and c["rank"] == "genus":
            c["existing_genus_level_plant_ids"] = sorted(by_genus.get(acc, []))
        c["database_status"] = ("species_already_in_database" if c["existing_plant_ids"] else "genus_level_record_in_database" if c["existing_genus_level_plant_ids"] else
                                "not_in_database" if c["rank"] in ("species", "genus") and acc else "unresolved_name_not_a_candidate")
        c["generalisation_note"] = "Evidence is listed per tortoise taxon. A record for one tortoise taxon is not evidence for another."

    # nutrient view for values already held
    view = []
    for r in nut:
        vals = {(v["nutrient_name"], v["nutrient_unit"]): v for v in r["values"]}
        row = {"record_id": r["record_id"], "analyzed_taxon": r["analyzed_taxon"], "analyzed_part": r["analyzed_part"], "preparation_state": r["preparation_state"],
               "source_url": r["source_url"], "match_to_candidate": r.get("match_to_candidate", "same_species"), "values": {}}
        for lab in ("calcium", "phosphorus", "crude fibre", "ndf", "adf", "lignin", "crude protein", "potassium", "oxalic acid", "nitrate", "tannins (eq. tannic acid)"):
            for (n, u), v in vals.items():
                if n == lab:
                    row["values"]["%s [%s, %s]" % (n, u, v["measurement_basis"])] = v["nutrient_value"]
        ca, ph = vals.get(("calcium", "g/kg DM")), vals.get(("phosphorus", "g/kg DM"))
        if ca and ph and ph["nutrient_value"] > 0:
            row["calcium_to_phosphorus"] = {"value": round(ca["nutrient_value"] / ph["nutrient_value"], 2), "derived_by_this_layer": True,
                                            "from": "calcium %s and phosphorus %s g/kg DM (means over %s and %s samples)" % (ca["nutrient_value"], ph["nutrient_value"], ca["sample_count"], ph["sample_count"]),
                                            "caution": "A quotient of two table means from different numbers of samples, computed here and not printed by the source. It describes this feed table only and is not a feeding rule."}
        if row["values"]:
            view.append(row)

    def cc(cs):
        new = [c for c in cs if c["database_status"] == "not_in_database"]
        return {"plant_names": len(cs), "new_candidates_not_in_database": len(new), "new_candidates_species_level": sum(c["rank"] == "species" for c in new),
                "new_candidates_genus_level": sum(c["rank"] == "genus" for c in new),
                "species_already_in_database": sum(c["database_status"] == "species_already_in_database" for c in cs),
                "genus_level_record_in_database": sum(c["database_status"] == "genus_level_record_in_database" for c in cs),
                "unresolved_not_a_candidate": sum(c["database_status"] == "unresolved_name_not_a_candidate" for c in cs)}

    tiers_all = Counter(e.get("evidence_tier") or tier_of(e) for e in all_ev if e["evidence_id"] not in on_hold_ids)
    per_tortoise = {}
    for e in all_ev:
        if e["evidence_id"] in on_hold_ids:
            continue
        t = per_tortoise.setdefault(e["tortoise_scientific_name"], {"records": 0, "species_specific": e.get("species_specific", True), "by_tier": Counter(), "added_in_unit_3": 0})
        t["records"] += 1
        t["by_tier"][e.get("evidence_tier") or tier_of(e)] += 1
        t["added_in_unit_3"] += e.get("unit") == 3
    for t in per_tortoise.values():
        t["by_tier"] = dict(sorted(t["by_tier"].items()))
    summary = {
        "unit_3_added": {"sources_read": len(sources), "sources_with_plant_records": sum(1 for s in sources if s["plant_record_count"]),
                         "sources_by_language": dict(sorted(Counter(s["language"] for s in sources).items())),
                         "sources_by_type": dict(sorted(Counter(s["source_type"] for s in sources).items())),
                         "evidence_records": len(evidence), "evidence_by_tier": dict(sorted(Counter(e["evidence_tier"] for e in evidence).items())),
                         "evidence_species_specific": sum(e["species_specific"] for e in evidence), "evidence_not_species_specific": sum(not e["species_specific"] for e in evidence),
                         "negative_records_by_kind": dict(sorted(Counter(e["negative_kind"] for e in evidence if e["negative_kind"]).items())),
                         "hazard_statements": len(hazards), "record_corrections": len(corrections)},
        "cumulative": {"evidence_records": len(all_ev), "evidence_records_on_hold_after_correction": len(on_hold_ids), "evidence_by_tier": dict(sorted(tiers_all.items())),
                       "tortoise_taxa_or_groups_with_evidence": len(per_tortoise), "candidates": cc(list(cands.values())), "candidates_in_unit_2": cc(cand2)},
        "per_tortoise": dict(sorted(per_tortoise.items())),
        "unit_1_records_after_unit_3": dict(sorted(Counter(r["status_after_unit_3"] for r in ledger).items())),
        "name_resolution": {"names_reviewed": len(resolutions), "by_decision": dict(sorted(Counter(r["decision"] for r in resolutions).items()))},
        "nutrient_view": {"records": len(view), "with_calcium_and_phosphorus": sum("calcium_to_phosphorus" in r for r in view),
                          "with_oxalate_or_tannin_values": sum(any(k.startswith(("oxalic", "tannins", "nitrate")) for k in r["values"]) for r in view)},
        "gaps_not_filled": tr["gaps_not_filled"],
    }
    meta = {"schema_version": "3.0", "generated_by": "scripts/build_global_plant_evidence_research_v3.py", "generated_from": "data/research/global_plant_evidence_transcription_v3.json",
            "extends": "the v1 and v2 research files, which are not modified", "layer": "research_only_not_published", "grade_policy": v1.GRADE_POLICY}
    dump(RES / "global_evidence_sources_v3.json", {**meta, "sources": sources, "cited_primary_status": tr["cited_primary_status"], "on_hold": tr["sources_on_hold"]})
    dump(RES / "tortoise_species_registry_v3.json", {**meta, "name_authority": "GBIF backbone taxonomy, species/match API", "species_added": registry,
                                                   "groups_not_species_specific": [{"tortoise_key": k, **g} for k, g in groups.items()]})
    dump(RES / "tortoise_plant_evidence_v3.json", {**meta, "evidence_tiers": TIER_KO, "records": evidence})
    dump(RES / "primary_verification_ledger_v3.json", {**meta, "note": "A unit-1 record counts as confirmed only when the cited publication itself was read. 'cited_source_read_does_not_support_the_statement' means the cited publication was read and does not contain the feeding statement.", "records": ledger})
    dump(RES / "record_corrections_v3.json", {**meta, "table_recheck": tr["table_recheck"], "corrections": corrections})
    dump(RES / "plant_name_resolutions_v3.json", {**meta, "first_database": "GBIF backbone taxonomy", "second_database": "World Flora Online plant list (matching service)", "resolutions": resolutions})
    dump(RES / "plant_candidates_v3.json", {**meta, "scope": "cumulative over units 1 to 3", "evidence_tiers": TIER_KO, "candidates": sorted(cands.values(), key=lambda c: c["candidate_key"])})
    dump(RES / "plant_hazard_statements_v3.json", {**meta, "note": "Statements made by sources that were read. They are not toxicity findings for tortoises.", "statements": hazards})
    dump(RES / "nutrient_safety_view_v3.json", {**meta, "note": "A layout of values already in the v1 and v2 nutrition files. %d records hold a tannin, oxalate or nitrate value (Feedipedia livestock feed tables; not tortoise measurements). A nutrient value is not a safety statement." % sum(any(k.startswith(("oxalic", "tannins", "nitrate")) for k in r["values"]) for r in view), "records": view})
    dump(RES / "research_layer_summary_v3.json", {**meta, "summary": summary})
    print("unit 3: sources %d, evidence %d, resolutions %d (resolved %d), candidates %d, hazards %d, nutrient view %d"
          % (len(sources), len(evidence), len(resolutions), len(res_by_name), len(cands), len(hazards), len(view)))


if __name__ == "__main__":
    main()
