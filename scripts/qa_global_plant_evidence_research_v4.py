#!/usr/bin/env python3
"""Offline checks for the unit-4 research files in data/research (they extend the v1-v3 files, which stay unchanged).

Fails when
  * a file does not parse, a record lacks a required field, or an ID repeats within unit 4 or collides with units 1-3,
  * a built record differs from the hand transcription,
  * detection methods are mixed up: a husbandry recommendation labelled as an observation or fecal detection, a study record
    without a method, a 'not eaten' row not flagged as such, or a secondary citation of units 1-3 given an observation label,
  * duplicates: two records of one source that say the same thing (within unit 4 or across units), a source URL already used,
    or a publication listed as a duplicate data set that is also entered as a source,
  * a label transcribed as a common name carries a scientific name, an accepted name is given without a passed name check,
    a wrong evidence tier, or a group record marked species-specific,
  * the index does not hold every record of units 1-4 exactly once, or a candidate loses a unit-3 link or counts on-hold evidence,
  * a hazard statement has no record behind it or claims a test in tortoises,
  * the review queue omits an unread citation, an unresolved name or a conflict,
  * any object carries a feeding grade, or the stored summary differs from a recount.

It reads data/plants.json and the v1-v3 research files only to check links. It never writes.
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "data/research"
OLD = ["tortoise_plant_evidence_v1.json", "tortoise_plant_evidence_v2.json", "tortoise_plant_evidence_v3.json", "global_evidence_sources_v1.json", "global_evidence_sources_v2.json",
       "global_evidence_sources_v3.json", "tortoise_species_registry_v1.json", "tortoise_species_registry_v2.json", "tortoise_species_registry_v3.json", "plant_candidates_v3.json",
       "primary_verification_ledger_v3.json", "record_corrections_v3.json", "plant_name_resolutions_v3.json"]
NEW = ["global_plant_evidence_transcription_v4.json", "global_evidence_sources_v4.json", "tortoise_species_registry_v4.json", "tortoise_plant_evidence_v4.json",
       "plant_hazard_statements_v4.json", "evidence_index_v4.json", "plant_candidates_v4.json", "review_queue_v4.json", "research_layer_summary_v4.json"]
REQUIRED = ["evidence_id", "source_id", "source_url", "source_citation", "source_language", "source_page", "tortoise_key", "tortoise_scientific_name", "plant_name_as_printed",
            "plant_name_check", "plant_part", "preparation_state", "wild_or_captive", "locality", "observed_consumption", "study_method", "detection_methods", "evidence_class",
            "evidence_type", "evidence_directness", "evidence_tier", "limitations", "verification_status"]
STATUS = {"peer_reviewed_field_study": "verified_primary_source", "university_thesis_field_study": "verified_primary_source_thesis",
          "keeper_organisation_web_page": "verified_keeper_organisation_page", "veterinary_reference_text": "verified_veterinary_reference"}
STUDY = ("peer_reviewed_field_study", "university_thesis_field_study")
STUDY_METHODS = {"direct_feeding_observation", "incidental_observation", "fecal_macroscopic", "fecal_histological", "not_detected_by_any_method"}
ADVICE_METHODS = {"husbandry_recommendation", "unreferenced_general_statement"}
OBSERVATION_LABELS = {"direct_feeding_observation", "incidental_observation", "fecal_macroscopic", "fecal_histological", "fecal_detection",
                      "direct_observation_and_fecal_analysis_not_separated", "fecal_dna_or_morphology_and_observation_see_quantity"}
OK_NAME = ("accepted", "synonym_of_accepted_name", "genus_kept_as_printed_backbone_status_synonym", "genus_kept_as_printed_backbone_status_doubtful", "exact_match_status_doubtful")
COMMON = r"common names? only|common name as printed|local name only|food group only|plant group only|unidentified|not identified"


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
    tr = d["global_plant_evidence_transcription_v4.json"]
    plants = {p["id"]: p for p in json.loads((ROOT / "data/plants.json").read_text(encoding="utf-8"))}
    old_ev = {e["evidence_id"]: e for i in (1, 2, 3) for e in d["tortoise_plant_evidence_v%d.json" % i]["records"]}
    ev4 = d["tortoise_plant_evidence_v4.json"]["records"]
    tortoises = {t["tortoise_key"]: t["scientific_name"] for t in d["tortoise_species_registry_v1.json"]["species"] + d["tortoise_species_registry_v2.json"]["species_added"]
                 + d["tortoise_species_registry_v3.json"]["species_added"]}
    groups = {g["tortoise_key"] for g in d["tortoise_species_registry_v3.json"]["groups_not_species_specific"] + d["tortoise_species_registry_v4.json"]["groups_not_species_specific"]}
    if groups & set(tortoises):
        errors.append("a group key clashes with a species key")

    old_sources = {s["source_id"]: s for i in (1, 2, 3) for s in d["global_evidence_sources_v%d.json" % i]["sources"]}
    sdoc = d["global_evidence_sources_v4.json"]
    sources = {s["source_id"]: s for s in sdoc["sources"]}
    if len(sources) != len(sdoc["sources"]) or list(sources) != list(tr["sources"]) or set(sources) & set(old_sources):
        errors.append("unit-4 sources do not match the transcription or reuse an earlier source ID")
    used_urls = {s["url"] for s in old_sources.values()}
    for s in sdoc["sources"]:
        sid = s["source_id"]
        if not str(s.get("url") or "").startswith("https://") or s["url"] in used_urls:
            errors.append("source %s: URL missing, not https, or already a source in units 1-3" % sid)
        used_urls.add(s["url"])
        if STATUS.get(s["source_type"]) != s["verification_status"] or s["access"] != "full_text_read":
            errors.append("source %s: status does not follow from its type, or it was not read in full" % sid)
        for k in ("citation", "method", "what_was_read", "language", "study_country"):
            if not s.get(k):
                errors.append("source %s: %s missing" % (sid, k))
        if s.get("year") is None and "year" not in s["what_was_read"]:
            errors.append("source %s: no year and no note saying the source gives none" % sid)
    for dup in sdoc["duplicate_datasets"]:
        if dup["same_dataset_as_source_id"] not in old_sources and dup["same_dataset_as_source_id"] not in sources:
            errors.append("duplicate data set points to an unknown source")
        if dup["url"] in used_urls or not dup.get("evidence") or not dup.get("decision"):
            errors.append("a publication listed as a duplicate data set is also entered as a source, or lacks its evidence and decision")

    ids = [e["evidence_id"] for e in ev4]
    expected = [("%s-%03d" % (sid, i), row) for sid, s in tr["sources"].items() for i, row in enumerate(s["records"], 1)]
    if [x[0] for x in expected] != ids or len(set(ids)) != len(ids) or set(ids) & set(old_ev):
        errors.append("evidence records do not match the transcription, repeat, or collide with units 1-3")
    rows, seen = dict(expected), set()
    for e in ev4:
        eid = e["evidence_id"]
        for k in REQUIRED:
            if e.get(k) in (None, "", []):
                errors.append("%s: %s missing" % (eid, k))
        s = sources.get(e["source_id"])
        if not s:
            errors.append("%s: unknown source" % eid)
            continue
        if e["verification_status"] != s["verification_status"] or e["source_url"] != s["url"] or e["source_citation"] != s["citation"]:
            errors.append("%s: status, URL or citation differs from its source" % eid)
        is_group = e["tortoise_key"] in groups
        if (not is_group and tortoises.get(e["tortoise_key"]) != e["tortoise_scientific_name"]) or e["species_specific"] == is_group:
            errors.append("%s: tortoise taxon unknown or species_specific flag wrong" % eid)
        row = rows.get(eid)
        if row:
            if [row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[9], row[12]] != [
                    e["tortoise_key"], e["plant_name_as_printed"], e["plant_part"], e["preparation_state"], e["wild_or_captive"], e["observed_consumption"],
                    e["quantity_as_reported"], e["locality"], e["source_page"], e["detection_methods"]]:
                errors.append("%s: differs from the transcription" % eid)
            typ = row[10]
            if e["evidence_class"] != {8: "institutional_husbandry_guideline", 9: "keeper_organisation_statement"}.get(typ, "wild_feeding_study") \
                    or e["evidence_directness"] != ("statement_of_the_source_read" if typ in (8, 9) else "primary_study_read"):
                errors.append("%s: evidence class or directness does not follow the transcribed evidence type" % eid)
            if re.search(COMMON, row[11] or "") and (e["plant_accepted_name"] or e["plant_name_check"] != "common_name_only_not_resolved"):
                errors.append("%s: a label transcribed as a common name carries a scientific name" % eid)
        m = set(e["detection_methods"])
        if e["evidence_directness"] == "primary_study_read":
            if s["source_type"] not in STUDY or not m <= STUDY_METHODS:
                errors.append("%s: a study record needs a study source and observation or fecal methods (has %s)" % (eid, sorted(m)))
        elif not m <= ADVICE_METHODS:
            errors.append("%s: advice from a guideline or keeper page is labelled with an observation or fecal method" % eid)
        not_eaten = m == {"not_detected_by_any_method"}
        if ("not_detected_by_any_method" in m and len(m) > 1) or not_eaten != (e["negative_kind"] == "not_eaten_in_study") or (not_eaten and not e["is_negative_record"]):
            errors.append("%s: 'not eaten' rows must carry only that method and the matching negative flag" % eid)
        if e["evidence_tier"] != tier(e):
            errors.append("%s: evidence tier %s, expected %s" % (eid, e["evidence_tier"], tier(e)))
        if e["plant_accepted_name"] and e["plant_name_check"] not in OK_NAME:
            errors.append("%s: accepted name given although the name check is %s" % (eid, e["plant_name_check"]))
        key = (e["source_id"], e["tortoise_key"], e["plant_name_as_printed"], e["plant_part"], e["preparation_state"], e["wild_or_captive"], e["locality"])
        if key in seen:
            errors.append("%s: duplicate of another record from the same source" % eid)
        seen.add(key)

    # index over units 1-4
    index = d["evidence_index_v4.json"]["records"]
    all_ev = {**old_ev, **{e["evidence_id"]: e for e in ev4}}
    held = {c["evidence_id"] for c in d["record_corrections_v3.json"]["corrections"] if c["action"] == "put_on_hold"}
    if [x["evidence_id"] for x in index] != list(all_ev):
        errors.append("index: must hold every record of units 1-4 exactly once, in order")
    ledger = {r["v1_evidence_id"]: r["status_after_unit_3"] for r in d["primary_verification_ledger_v3.json"]["records"]}
    resolved = {r["name_as_printed"]: r["resolved_name"] for r in d["plant_name_resolutions_v3.json"]["resolutions"] if r["resolved_name"]}
    groups_seen = {}
    for x in index:
        e = all_ev.get(x["evidence_id"])
        if not e:
            continue
        iid = x["evidence_id"]
        if [x["tortoise_key"], x["plant_name_as_printed"], x["plant_part"], x["wild_or_captive"], x["evidence_directness"], x["source_id"]] != [
                e["tortoise_key"], e["plant_name_as_printed"], e["plant_part"], e["wild_or_captive"], e["evidence_directness"], e["source_id"]]:
            errors.append("index %s: differs from the unit record" % iid)
        if x["plant_accepted_name"] != (e["plant_accepted_name"] or resolved.get(e["plant_name_as_printed"])):
            errors.append("index %s: accepted name is neither the unit record's nor a unit-3 resolution" % iid)
        if x["on_hold"] != (iid in held) or x["evidence_tier"] != (e.get("evidence_tier") or tier(e)) or x["unit_1_citation_status"] != ledger.get(iid):
            errors.append("index %s: hold flag, tier or citation status wrong" % iid)
        if x["species_specific"] != (x["tortoise_key"] not in groups):
            errors.append("index %s: species_specific flag wrong" % iid)
        if not x["detection_methods"] or x["detection_method_recorded_per_record"] != bool(e.get("detection_methods")) or (e.get("detection_methods") and e["detection_methods"] != x["detection_methods"]):
            errors.append("index %s: detection method missing or not the record's own" % iid)
        m = set(x["detection_methods"])
        if e["evidence_directness"] in ("reported_in_account_primary_not_read", "reported_in_source_primary_not_read") and m != {"secondary_citation_method_not_verified"}:
            errors.append("index %s: a secondary citation is labelled with a method that was not verified" % iid)
        if x["evidence_tier"] in ("4_institutional_husbandry_guideline", "6_keeper_organisation_statement") and m & OBSERVATION_LABELS:
            errors.append("index %s: a guideline or keeper statement is labelled as an observation or fecal detection" % iid)
        if x["evidence_tier"] == "7_local_or_community_report" and m & OBSERVATION_LABELS:
            errors.append("index %s: a resident report is labelled as an observation or fecal detection" % iid)
        groups_seen.setdefault((x["source_id"], x["tortoise_key"], x["plant_name_as_printed"], x["plant_part"], e["preparation_state"], x["wild_or_captive"], e["locality"]), []).append(iid)
    for k, v in groups_seen.items():
        if len(v) > 1:
            errors.append("duplicate records across units: %s" % ", ".join(v))

    # corrected quantities, denominators, parts
    corr = {c["evidence_id"]: c for c in d["record_corrections_v3.json"]["corrections"]}
    dens = tr["denominators_by_source"]
    mg = tr["moorhouse_method_labels"]
    for x in index:
        iid, e = x["evidence_id"], all_ev.get(x["evidence_id"])
        if not e:
            continue
        c = corr.get(iid)
        want_q = (None if c["action"] == "put_on_hold" else c["corrected_quantity"]) if c else e.get("quantity_as_reported")
        if x["quantity_as_reported"] != want_q or bool(c) != bool(x["quantity_correction"]):
            errors.append("index %s: quantity is not the value after the unit-3 corrections" % iid)
        if c and x["detection_methods"] and set(x["detection_methods"]) & {"fecal_macroscopic", "fecal_detection"} and "dung morphology" not in (want_q or "").replace("dung-morphology value not determinable", ""):
            errors.append("index %s: corrected record still counted as a dung-morphology detection" % iid)
        if x["on_hold"] and x["detection_methods"] != ["not_determinable_record_on_hold"]:
            errors.append("index %s: a held record must not carry a detection method" % iid)
        if x["source_id"] == "moorhouse_gann_2022" and not x["on_hold"]:
            labs = {mg[lab] for lab, n in re.findall(r"(DNA metabarcoding|dung morphology|feeding observation) (\d+) of", want_q or "") if int(n) > 0}
            if "stated in the article text" in (want_q or ""):
                labs.add("statement_in_article_text")
            if set(x["detection_methods"]) != labs:
                errors.append("index %s: methods %s do not follow the corrected quantity text" % (iid, x["detection_methods"]))
        dd = dens.get(x["source_id"])
        if dd and want_q:
            for m in re.finditer(r"(?:(DNA metabarcoding|dung morphology|feeding observation) )?(\d+) of (?:the )?(\d+)(?: ([a-z ]+?))?(?: \(([\d.]+)%\))?(?:[;,]|$)", want_q):
                lab, num, den, what, pct = m.group(1), int(m.group(2)), int(m.group(3)), (m.group(4) or "").strip(), m.group(5)
                allowed = set(dd["labels"].values())
                if num > den or den not in allowed:
                    errors.append("index %s: '%s' has a numerator above the denominator or a denominator the source does not use" % (iid, m.group(0)))
                elif lab and dd["labels"].get(lab) != den:
                    errors.append("index %s: %s counted out of %d, the source uses %s" % (iid, lab, den, dd["labels"].get(lab)))
                elif pct and dd["percent_is_count_over_denominator"] and abs(num * 100.0 / den - float(pct)) > 0.01:
                    errors.append("index %s: %s%% is not %d/%d" % (iid, pct, num, den))
        if re.search(r"seeds found", e["observed_consumption"]) and "seed" not in e["plant_part"]:
            errors.append("index %s: a seed-based record must name seeds as the part" % iid)
        if not str(e["plant_part"]).strip():
            errors.append("index %s: plant part empty (use 'not stated')" % iid)

    # candidates
    cands = d["plant_candidates_v4.json"]["candidates"]
    cmap = {c["candidate_key"]: c for c in cands}
    acc = Counter(c["accepted_name"] for c in cands if c["accepted_name"])
    if len(cmap) != len(cands) or any(k > 1 for k in acc.values()):
        errors.append("duplicate candidate key or accepted name")
    ix = {x["evidence_id"]: x for x in index}
    where = set()
    for c in cands:
        live = [i for i in c["evidence_ids"] if i not in held]
        where.update(c["evidence_ids"])
        if any(i not in ix for i in c["evidence_ids"]) or sorted(i for i in c["evidence_ids"] if i in held) != c["evidence_ids_on_hold"]:
            errors.append("candidate %s: unknown evidence or on-hold evidence not listed as on hold" % c["candidate_key"])
            continue
        if Counter(ix[i]["evidence_tier"] for i in live) != Counter(c["evidence_by_tier"]) or {s["tortoise_key"] for s in c["tortoise_scope"]} != {ix[i]["tortoise_key"] for i in live}:
            errors.append("candidate %s: tier counts or tortoise scope differ from its live evidence" % c["candidate_key"])
        for s in c["tortoise_scope"]:
            if s["species_specific"] == (s["tortoise_key"] in groups) or s["eaten_records"] + s["not_eaten_or_avoided_records"] != sum(ix[i]["tortoise_key"] == s["tortoise_key"] for i in live):
                errors.append("candidate %s: scope %s has a wrong flag or count" % (c["candidate_key"], s["tortoise_key"]))
        if any(p not in plants for p in c["existing_plant_ids"] + c["existing_genus_level_plant_ids"]) or (c["database_status"] == "not_in_database" and not c["accepted_name"]):
            errors.append("candidate %s: unknown plant id, or an unresolved name listed as a new candidate" % c["candidate_key"])
    for i in all_ev:
        if i not in where:
            errors.append("%s: not linked to any candidate" % i)
    for c3 in d["plant_candidates_v3.json"]["candidates"]:
        c4 = cmap.get(c3["candidate_key"])
        if not c4 or not set(c3["evidence_ids"]) <= set(c4["evidence_ids"]) or not set(c3["seed_mixture_ids"]) <= set(c4["seed_mixture_ids"]) \
                or not set(c3["forage_nutrition_record_ids"]) <= set(c4["forage_nutrition_record_ids"]) or not set(c3["names_as_printed"]) <= set(c4["names_as_printed"]):
            errors.append("unit-3 candidate %s is missing or lost a link" % c3["candidate_key"])

    for h in d["plant_hazard_statements_v4.json"]["statements"]:
        if sorted({all_ev[i]["plant_name_as_printed"] for i in h["evidence_ids"] if i in all_ev}) != sorted(set(h["applies_to_records_named"])):
            errors.append("hazard %s: the linked records do not carry exactly the plant names the statement covers" % h["hazard_id"])
        if not h["evidence_ids"] or any(i not in all_ev or all_ev[i]["source_id"] != h["source_id"] for i in h["evidence_ids"]):
            errors.append("hazard %s: no evidence record from the same source behind it" % h["hazard_id"])
        if h["tested_in_tortoises_by_this_source"] is not False or not h.get("what_it_does_not_establish") or not h.get("location") or h["source_id"] not in sources:
            errors.append("hazard %s: must state its location, a read source, and that it is not a tortoise test" % h["hazard_id"])

    # review queue
    q = d["review_queue_v4.json"]["queue"]
    unread = [i for i, s in ledger.items() if s == "secondary_citation_primary_not_read"]
    if sorted(r["v1_evidence_id"] for r in q["unit_1_citations_not_read"]) != sorted(unread):
        errors.append("review queue: unread citations differ from the ledger")
    need = {x["plant_name_as_printed"] for x in index if not x["plant_accepted_name"] and x["plant_name_check"] not in ("common_name_only_not_resolved", "accepted")}
    if {n["name_as_printed"] for n in q["names_needing_review"]} != need:
        errors.append("review queue: names needing review differ from the index")
    pairs = {}
    for x in index:
        if x["plant_accepted_name"] and not x["on_hold"]:
            pairs.setdefault((x["tortoise_key"], x["plant_accepted_name"]), set()).add(x["is_negative_record"])
    conflicts = {k for k, v in pairs.items() if v == {True, False}}
    if {(c["tortoise_key"], c["plant_accepted_name"]) for c in q["conflicting_records_same_tortoise_and_plant"]} != conflicts:
        errors.append("review queue: conflicting records differ from a recount")
    gf = {}
    for x in index:
        fam = all_ev[x["evidence_id"]].get("plant_family")
        if x["plant_accepted_name"] and fam and x["name_from"] == "unit_record":
            gf.setdefault(x["plant_accepted_name"].split()[0], set()).add(fam)
    if sorted(g["genus"] for g in q["genus_with_more_than_one_backbone_family"]) != sorted(g for g, f in gf.items() if len(f) > 1):
        errors.append("review queue: genera mapped to more than one family differ from a recount")
    if {r["evidence_id"] for r in q["records_on_hold"]} != held or q["identical_record_groups_across_units"]:
        errors.append("review queue: holds differ from the corrections file, or identical records exist across units")

    sm = d["research_layer_summary_v4.json"]["summary"]
    live = [x for x in index if not x["on_hold"]]
    for name, stored, counted in [
            ("unit-4 evidence", sm["unit_4_added"]["evidence_records"], len(ev4)), ("cumulative evidence", sm["cumulative"]["evidence_records"], len(index)),
            ("plant names", sm["cumulative"]["candidates"]["plant_names"], len(cands)),
            ("new candidates", sm["cumulative"]["candidates"]["new_candidates_not_in_database"], sum(c["database_status"] == "not_in_database" for c in cands)),
            ("methods", sm["cumulative"]["evidence_by_detection_method"], dict(sorted(Counter(m for x in live for m in x["detection_methods"]).items()))),
            ("tiers", sm["cumulative"]["evidence_by_tier"], dict(sorted(Counter(x["evidence_tier"] for x in live).items()))),
            ("per-tortoise total", sum(t["records"] for t in sm["per_tortoise"].values()), len(live))]:
        if stored != counted:
            errors.append("summary: %s is stored as %s but recounts to %s" % (name, stored, counted))

    report(errors, "research layer unit-4 QA ok: %d sources, %d evidence records (%d species-specific), %d cumulative, %d candidates, %d names and %d citations in the review queue, no duplicate records"
           % (len(sources), len(ev4), sum(e["species_specific"] for e in ev4), len(index), len(cands), len(q["names_needing_review"]), len(q["unit_1_citations_not_read"])))


def report(errors, ok=None):
    if errors:
        print("research layer unit-4 QA failed (%d):" % len(errors))
        for e in errors[:80]:
            print(" -", e)
        sys.exit(1)
    if ok:
        print(ok)


if __name__ == "__main__":
    main()
