#!/usr/bin/env python3
"""Offline checks for the unit-3 research files in data/research (they extend the v1 and v2 files, which stay unchanged).

Fails when
  * a file does not parse, a record lacks a required field (source URL, citation, page or table, tortoise, plant part, limits),
    or an ID repeats within unit 3 or collides with units 1-2,
  * a built record differs from the hand transcription,
  * evidence is overstated: a husbandry guideline or keeper statement marked as a study that was read, a wrong evidence tier,
    a record of a non-specific tortoise group marked species-specific, or a unit-1 citation marked confirmed without a
    publication read in full and a matching record,
  * a label the transcription calls a common name gets a scientific name, or a name is resolved without both databases' results,
  * a unit-2 record put on hold still counts as live evidence for a candidate, or a unit-1/unit-2 candidate link is lost,
  * a hazard statement has no evidence record behind it or claims a test in tortoises,
  * a calcium-to-phosphorus quotient is not flagged as derived or does not follow from the two stored values,
  * any object in the unit-3 files carries a feeding grade,
  * the stored summary differs from a recount.

It reads data/plants.json and the v1/v2 research files only to check links. It never writes.
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "data/research"
OLD = ["tortoise_plant_evidence_v1.json", "tortoise_plant_evidence_v2.json", "global_evidence_sources_v1.json", "global_evidence_sources_v2.json",
       "tortoise_species_registry_v1.json", "tortoise_species_registry_v2.json", "plant_candidates_v2.json", "primary_verification_ledger_v2.json",
       "forage_nutrition_research_v1.json", "forage_nutrition_research_v2.json"]
NEW = ["global_plant_evidence_transcription_v3.json", "global_evidence_sources_v3.json", "tortoise_species_registry_v3.json", "tortoise_plant_evidence_v3.json",
       "primary_verification_ledger_v3.json", "record_corrections_v3.json", "plant_name_resolutions_v3.json", "plant_candidates_v3.json",
       "plant_hazard_statements_v3.json", "nutrient_safety_view_v3.json", "research_layer_summary_v3.json"]
REQUIRED = ["evidence_id", "source_id", "source_url", "source_citation", "source_language", "source_page", "tortoise_key", "tortoise_scientific_name",
            "plant_name_as_printed", "plant_name_check", "plant_part", "preparation_state", "wild_or_captive", "locality", "observed_consumption", "study_method",
            "evidence_class", "evidence_type", "evidence_directness", "evidence_tier", "limitations", "verification_status"]
STATUS = {"peer_reviewed_field_study": "verified_primary_source", "peer_reviewed_monograph": "verified_primary_source",
          "society_journal_field_study": "verified_primary_source_society_journal", "university_repository_paper": "verified_primary_source_repository_paper",
          "government_technical_report": "verified_document_no_feeding_content", "zoo_association_husbandry_guideline": "verified_husbandry_guideline",
          "museum_veterinary_husbandry_guideline": "verified_husbandry_guideline", "keeper_organisation_web_page": "verified_keeper_organisation_page"}
STUDY = ("peer_reviewed_field_study", "peer_reviewed_monograph", "society_journal_field_study", "university_repository_paper")
OK_NAME = ("accepted", "synonym_of_accepted_name", "genus_kept_as_printed_backbone_status_synonym", "genus_kept_as_printed_backbone_status_doubtful", "exact_match_status_doubtful")
LEDGER = {"confirmed_in_primary", "confirmed_with_difference", "primary_read_in_unit_1", "secondary_citation_primary_not_read", "statement_of_the_source_no_primary_cited",
          "not_in_the_cited_source_read_other_cited_sources_unread", "cited_source_read_does_not_support_the_statement"}
RESOLVED = ("resolved_orthographic_variant", "resolved_by_second_database", "resolved_homonym_by_author_printed_in_source", "resolved_by_source_context",
            "resolved_source_and_second_database_treat_as_distinct")
COMMON = r"common names? only|common name as printed|local name only|food group only|plant group only|unidentified|not identified"


def lev(a, b):
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def tier(e):
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


def grades(obj, path, errors):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in ("feeding_grade", "grade", "verdict") and v is not None:
                errors.append("%s carries %s = %r" % (path, k, v))
            grades(v, path, errors)
    elif isinstance(obj, list):
        for v in obj:
            grades(v, path, errors)


def main():
    errors, d = [], {}
    for f in OLD + NEW:
        try:
            d[f] = json.loads((RES / f).read_text(encoding="utf-8"))
        except Exception as e:  # noqa: BLE001
            errors.append("%s: %s" % (f, e))
    if errors:
        report(errors)
    for f in NEW[1:]:
        grades(d[f], f, errors)
    tr = d["global_plant_evidence_transcription_v3.json"]
    plants = {p["id"]: p for p in json.loads((ROOT / "data/plants.json").read_text(encoding="utf-8"))}
    ev1, ev2 = d["tortoise_plant_evidence_v1.json"]["records"], d["tortoise_plant_evidence_v2.json"]["records"]
    ev3 = d["tortoise_plant_evidence_v3.json"]["records"]
    old_ev = {e["evidence_id"]: e for e in ev1 + ev2}
    all_ev = {**old_ev, **{e["evidence_id"]: e for e in ev3}}
    tortoises = {t["tortoise_key"]: t["scientific_name"] for t in d["tortoise_species_registry_v1.json"]["species"] + d["tortoise_species_registry_v2.json"]["species_added"]}
    reg = d["tortoise_species_registry_v3.json"]
    for t in reg["species_added"]:
        if t["tortoise_key"] in tortoises or t["name_check"] != "accepted":
            errors.append("tortoise %s: duplicate key or name check %s" % (t["scientific_name"], t["name_check"]))
        tortoises[t["tortoise_key"]] = t["scientific_name"]
    groups = {g["tortoise_key"]: g for g in reg["groups_not_species_specific"]}
    for k, g in groups.items():
        if k in tortoises or any(m not in tortoises for m in g["member_tortoise_keys"]):
            errors.append("group %s: clashes with a species key or names an unknown member" % k)

    old_sources = {s["source_id"]: s for s in d["global_evidence_sources_v1.json"]["sources"] + d["global_evidence_sources_v2.json"]["sources"]}
    slist = d["global_evidence_sources_v3.json"]["sources"]
    sources = {s["source_id"]: s for s in slist}
    if len(sources) != len(slist) or list(sources) != list(tr["sources"]) or set(sources) & set(old_sources):
        errors.append("unit-3 sources do not match the transcription or reuse an earlier source ID")
    old_urls = {s["url"] for s in old_sources.values()}
    for s in slist:
        sid = s["source_id"]
        if not str(s.get("url") or "").startswith("https://") or s["url"] in old_urls:
            errors.append("source %s: URL missing, not https, or already a source in units 1-2" % sid)
        if STATUS.get(s["source_type"]) != s["verification_status"] or s["access"] != "full_text_read":
            errors.append("source %s: status does not follow from its type, or it was not read in full" % sid)
        for k in ("citation", "method", "what_was_read", "language", "study_country"):
            if not s.get(k):
                errors.append("source %s: %s missing" % (sid, k))
        if s.get("year") is None and "year" not in s["what_was_read"]:
            errors.append("source %s: no year and no note saying the source gives none" % sid)

    ids = [e["evidence_id"] for e in ev3]
    expected = [("%s-%02d" % (sid, i), row) for sid, s in tr["sources"].items() for i, row in enumerate(s["records"], 1)]
    if [x[0] for x in expected] != ids or len(set(ids)) != len(ids) or set(ids) & set(old_ev):
        errors.append("evidence records do not match the transcription, repeat, or collide with units 1-2")
    rows, seen = dict(expected), set()
    for e in ev3:
        eid = e["evidence_id"]
        for k in REQUIRED:
            if e.get(k) in (None, ""):
                errors.append("%s: %s missing" % (eid, k))
        s = sources.get(e["source_id"])
        if not s:
            errors.append("%s: unknown source" % eid)
            continue
        if e["verification_status"] != s["verification_status"] or e["source_url"] != s["url"] or e["source_citation"] != s["citation"]:
            errors.append("%s: status, URL or citation differs from its source" % eid)
        is_group = e["tortoise_key"] in groups
        if not is_group and tortoises.get(e["tortoise_key"]) != e["tortoise_scientific_name"]:
            errors.append("%s: tortoise taxon not in a registry" % eid)
        if e["species_specific"] == is_group:
            errors.append("%s: species_specific does not match its tortoise key" % eid)
        row = rows.get(eid)
        if row:
            if [row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[9]] != [e["tortoise_key"], e["plant_name_as_printed"], e["plant_part"], e["preparation_state"],
                                                                                             e["wild_or_captive"], e["observed_consumption"], e["quantity_as_reported"], e["locality"], e["source_page"]]:
                errors.append("%s: differs from the transcription" % eid)
            typ = row[10]
            want_cls = {8: "institutional_husbandry_guideline", 9: "keeper_organisation_statement", 5: "husbandry_practice"}.get(typ, "wild_feeding_study")
            want_dir = ("statement_of_the_source_read" if typ in (8, 9) else "husbandry_note_in_primary_source_read" if typ == 5 else
                        "primary_study_read" if s["source_type"] in STUDY else "statement_of_the_source_read")
            if e["evidence_class"] != want_cls or e["evidence_directness"] != want_dir:
                errors.append("%s: evidence class or directness does not follow the transcribed evidence type and source type" % eid)
            want_neg = "source_advises_against" if re.search(r"advises against", row[5]) else "animal_avoided_or_refused" if re.search(r"avoid|reject|refus", row[5]) else None
            if e["negative_kind"] != want_neg or e["is_negative_record"] != bool(want_neg):
                errors.append("%s: negative-record fields do not follow the transcribed statement" % eid)
            if re.search(COMMON, row[11] or "") and (e["plant_accepted_name"] or e["plant_name_check"] != "common_name_only_not_resolved"):
                errors.append("%s: a label transcribed as a common name carries a scientific name" % eid)
        if e["evidence_directness"] == "primary_study_read" and (s["source_type"] not in STUDY or e["primary_reference_cited_by_source"]):
            errors.append("%s: marked primary_study_read without a study read in full" % eid)
        if e["evidence_tier"] != tier(e):
            errors.append("%s: evidence tier %s, expected %s" % (eid, e["evidence_tier"], tier(e)))
        if e["plant_accepted_name"] and e["plant_name_check"] not in OK_NAME:
            errors.append("%s: accepted name given although the name check is %s" % (eid, e["plant_name_check"]))
        key = (e["source_id"], e["tortoise_key"], e["plant_name_as_printed"], e["plant_part"], e["preparation_state"], e["wild_or_captive"], e["locality"])
        if key in seen:
            errors.append("%s: duplicate of another record from the same source" % eid)
        seen.add(key)

    # ledger
    ledger = d["primary_verification_ledger_v3.json"]["records"]
    prev = {r["v1_evidence_id"]: r for r in d["primary_verification_ledger_v2.json"]["records"]}
    declared = {x["v1_evidence_id"]: x for x in tr["primary_verification_of_v1_records"]}
    read_sources = {**old_sources, **sources}
    if [r["v1_evidence_id"] for r in ledger] != [e["evidence_id"] for e in ev1]:
        errors.append("ledger: must hold exactly one row per unit-1 evidence record, in order")
    for r in ledger:
        lid, st = r["v1_evidence_id"], r["status_after_unit_3"]
        if st not in LEDGER or lid not in prev:
            errors.append("ledger %s: unknown status" % lid)
            continue
        if lid not in declared and st != prev[lid]["status_after_unit_2"]:
            errors.append("ledger %s: status changed without an entry in the transcription" % lid)
        if lid in declared and st != declared[lid]["result"]:
            errors.append("ledger %s: status differs from the transcription" % lid)
        if prev[lid]["status_after_unit_2"].startswith("confirmed") and not st.startswith("confirmed"):
            errors.append("ledger %s: a confirmed record lost its status" % lid)
        if st.startswith("confirmed") or st.startswith("cited_source_read") or st.startswith("not_in_the_cited"):
            s = read_sources.get(r.get("primary_source_id"))
            if not s or s["access"] != "full_text_read":
                errors.append("ledger %s: %s without a publication read in full" % (lid, st))
        if st.startswith("confirmed"):
            c = all_ev.get(r.get("confirming_evidence_id"))
            if not c or c["source_id"] != r["primary_source_id"] or c["tortoise_key"] != all_ev[lid]["tortoise_key"]:
                errors.append("ledger %s: no matching record of the same tortoise in the publication that was read" % lid)
        if st.startswith("cited_source_read") and (r.get("confirming_evidence_id") or not r.get("note")):
            errors.append("ledger %s: a mismatch needs a note and must not point to a confirming record" % lid)
        if st == "secondary_citation_primary_not_read" and r.get("confirming_evidence_id"):
            errors.append("ledger %s: unread citation with a confirming record" % lid)

    # corrections
    corr = d["record_corrections_v3.json"]["corrections"]
    held = set()
    for c in corr:
        if c["evidence_id"] not in {e["evidence_id"] for e in ev2} or not c["reason"]:
            errors.append("correction %s: target not a unit-2 record, or no reason" % c["evidence_id"])
        if c["action"] == "put_on_hold":
            held.add(c["evidence_id"])
        elif c["action"] != "quantity_withdrawn" or not c["corrected_quantity"]:
            errors.append("correction %s: unknown action or missing corrected quantity" % c["evidence_id"])

    # name resolutions
    res = d["plant_name_resolutions_v3.json"]["resolutions"]
    resolved = {}
    for r in res:
        n = r["name_as_printed"]
        if (r["decision"] in RESOLVED) != bool(r["resolved_name"]):
            errors.append("name %s: decision %s and resolved name do not agree" % (n, r["decision"]))
        if r["resolved_name"]:
            if not r.get("second_database_result") or not r.get("gbif_result") or not r.get("reason"):
                errors.append("name %s: resolved without both databases' results and a reason" % n)
            resolved[n] = r["resolved_name"]
        if r["decision"] == "resolved_orthographic_variant" and lev(re.sub(r" (sp|spp)\.$", "", n).lower(), r["corrected_spelling"].lower()) > 2:
            errors.append("name %s: spelling correction changes more than two letters" % n)
        for i in r["applies_to_evidence_ids"]:
            if i not in all_ev or all_ev[i]["plant_name_as_printed"] != n:
                errors.append("name %s: evidence %s does not carry this name" % (n, i))

    # candidates
    cands = d["plant_candidates_v3.json"]["candidates"]
    cmap = {c["candidate_key"]: c for c in cands}
    acc = Counter(c["accepted_name"] for c in cands if c["accepted_name"])
    if len(cmap) != len(cands) or any(k > 1 for k in acc.values()):
        errors.append("duplicate candidate key or accepted name")
    where = {}
    for c in cands:
        for i in c["evidence_ids"]:
            if i not in all_ev:
                errors.append("candidate %s: unknown evidence %s" % (c["candidate_key"], i))
            where[i] = c
        live = [i for i in c["evidence_ids"] if i not in held]
        if sorted(i for i in c["evidence_ids"] if i in held) != c["evidence_ids_on_hold"]:
            errors.append("candidate %s: on-hold evidence not listed as on hold" % c["candidate_key"])
        if sum(c["evidence_by_tier"].values()) != len(live):
            errors.append("candidate %s: tier counts include on-hold or missing evidence" % c["candidate_key"])
        if Counter(all_ev[i].get("evidence_tier") or tier(all_ev[i]) for i in live if i in all_ev) != Counter(c["evidence_by_tier"]):
            errors.append("candidate %s: tier counts differ from its evidence" % c["candidate_key"])
        for s in c["tortoise_scope"]:
            if s["species_specific"] == (s["tortoise_key"] in groups):
                errors.append("candidate %s: tortoise scope %s has the wrong species-specific flag" % (c["candidate_key"], s["tortoise_key"]))
        if {s["tortoise_key"] for s in c["tortoise_scope"]} != {all_ev[i]["tortoise_key"] for i in live if i in all_ev}:
            errors.append("candidate %s: tortoise scope differs from its live evidence" % c["candidate_key"])
        for pid in c["existing_plant_ids"] + c["existing_genus_level_plant_ids"]:
            if pid not in plants:
                errors.append("candidate %s: unknown plant id %s" % (c["candidate_key"], pid))
        if c["database_status"] == "not_in_database" and not c["accepted_name"]:
            errors.append("candidate %s: unresolved name listed as a new candidate" % c["candidate_key"])
    for i in all_ev:
        if i not in where:
            errors.append("%s: not linked to any candidate" % i)
    for c2 in d["plant_candidates_v2.json"]["candidates"]:
        k = c2["candidate_key"]
        k3 = k if k in cmap else resolved.get(k[len("printed:"):]) if k.startswith("printed:") else None
        c3 = cmap.get(k3)
        if not c3 or not set(c2["evidence_ids"]) <= set(c3["evidence_ids"]) or not set(c2["seed_mixture_ids"]) <= set(c3["seed_mixture_ids"]) \
                or not set(c2["forage_nutrition_record_ids"]) <= set(c3["forage_nutrition_record_ids"]) or not set(c2["names_as_printed"]) <= set(c3["names_as_printed"]):
            errors.append("unit-2 candidate %s is missing or lost a link" % k)

    # hazard statements
    for h in d["plant_hazard_statements_v3.json"]["statements"]:
        if not h["evidence_ids"] or any(i not in all_ev or all_ev[i]["source_id"] != h["source_id"] for i in h["evidence_ids"]):
            errors.append("hazard %s: no evidence record from the same source behind it" % h["hazard_id"])
        if h["tested_in_tortoises_by_this_source"] is not False or not h.get("what_it_does_not_establish") or not h.get("location") or h["source_id"] not in read_sources:
            errors.append("hazard %s: must state its location, a read source, and that it is not a tortoise test" % h["hazard_id"])

    # nutrient view
    nut = {r["record_id"]: r for r in d["forage_nutrition_research_v1.json"]["records"] + d["forage_nutrition_research_v2.json"]["records"]}
    for r in d["nutrient_safety_view_v3.json"]["records"]:
        src = nut.get(r["record_id"])
        if not src:
            errors.append("nutrient view %s: unknown nutrition record" % r["record_id"])
            continue
        vals = {(v["nutrient_name"], v["nutrient_unit"]): v["nutrient_value"] for v in src["values"]}
        for k, v in r["values"].items():
            m = re.fullmatch(r"(.+) \[(.+), (.+)\]", k)
            if not m or vals.get((m.group(1), m.group(2))) != v:
                errors.append("nutrient view %s: %s differs from the nutrition file" % (r["record_id"], k))
        q = r.get("calcium_to_phosphorus")
        ca, ph = vals.get(("calcium", "g/kg DM")), vals.get(("phosphorus", "g/kg DM"))
        if q and (q.get("derived_by_this_layer") is not True or not ca or not ph or round(ca / ph, 2) != q["value"] or not q.get("caution")):
            errors.append("nutrient view %s: calcium-to-phosphorus quotient is not flagged as derived or does not follow from the stored values" % r["record_id"])

    sm = d["research_layer_summary_v3.json"]["summary"]
    for name, stored, counted in [
            ("unit-3 evidence", sm["unit_3_added"]["evidence_records"], len(ev3)), ("cumulative evidence", sm["cumulative"]["evidence_records"], len(all_ev)),
            ("on hold", sm["cumulative"]["evidence_records_on_hold_after_correction"], len(held)), ("plant names", sm["cumulative"]["candidates"]["plant_names"], len(cands)),
            ("new candidates", sm["cumulative"]["candidates"]["new_candidates_not_in_database"], sum(c["database_status"] == "not_in_database" for c in cands)),
            ("ledger", sm["unit_1_records_after_unit_3"], dict(sorted(Counter(r["status_after_unit_3"] for r in ledger).items()))),
            ("species-specific", sm["unit_3_added"]["evidence_species_specific"], sum(e["species_specific"] for e in ev3)),
            ("tiers", sm["cumulative"]["evidence_by_tier"], dict(sorted(Counter(e.get("evidence_tier") or tier(e) for i, e in all_ev.items() if i not in held).items())))]:
        if stored != counted:
            errors.append("summary: %s is stored as %s but recounts to %s" % (name, stored, counted))

    done = Counter(r["status_after_unit_3"] for r in ledger)
    report(errors, "research layer unit-3 QA ok: %d sources, %d evidence records (%d species-specific), %d cumulative; unit-1 citations confirmed %d, not supported %d, unread %d; %d names resolved of %d; %d candidates"
           % (len(slist), len(ev3), sum(e["species_specific"] for e in ev3), len(all_ev), done["confirmed_in_primary"] + done["confirmed_with_difference"],
              done["cited_source_read_does_not_support_the_statement"], done["secondary_citation_primary_not_read"], len(resolved), len(res), len(cands)))


def report(errors, ok=None):
    if errors:
        print("research layer unit-3 QA failed (%d):" % len(errors))
        for e in errors[:80]:
            print(" -", e)
        sys.exit(1)
    if ok:
        print(ok)


if __name__ == "__main__":
    main()
