#!/usr/bin/env python3
"""Pre-merge integration checks over the whole research layer (units 1-6) and the read-only public nutrition files.

Fails when
  * excluded nutrients come back: a value the page audit, a record's dropped list or the unit-5 exclusion audit excludes is kept
    in a research nutrition file or shown in the unit-3 nutrient view, a kept Feedipedia value has no printed sample count, or
    the nutrient view shows a value that is not kept in the v1/v2 nutrition files,
  * a public nutrition value is called matched (verified) although the page audit could not compare a sample count: 'matched'
    needs a stored count equal to a printed one; a value without a stored count must stay 'mean_matched_nb_not_stored', and a
    public record's verification text must not claim a sample count,
  * nutrition and feeding safety are mixed: a research nutrition record, nutrient view record or evidence record carries a feeding
    grade or verdict, the nutrient view or a hazard statement loses its 'does not establish' wording, a nutrition record carries a
    safety or toxicity field, or a public nutrition record is marked for use in a feeding verdict,
  * the database is inconsistent across units: an evidence, source, nutrition or hazard id repeats, a record names an unknown
    source or tortoise key, its tortoise name differs from the registry, its source URL or language differs from the source, an
    accepted plant name is not a well-formed name, a plant part is empty, a record claims to apply to other tortoise species, the
    unit-5 index differs from a unit record, or one English code has two Korean labels (or one label two codes).
It never writes.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "data/research"
NUTRITION = ("forage_nutrition_research_v1.json", "forage_nutrition_research_v2.json", "forage_nutrition_research_v5.json")
UNITS = range(1, 6)
SAFETY_WORDS = re.compile(r"safe|safety|toxic|verdict|grade|hazard|risk", re.I)
NAME = re.compile(r"[A-Z][a-z-]+( [a-z-]+)?( (subsp\.|var\.|f\.) [a-z-]+)?")
# a record may sit below its source's status (primary not read); see qa_global_plant_evidence_research_v2.py
DOWNGRADED_STATUS = {"reported_in_source_primary_not_read": "secondary_source_checked_primary_unread"}
# detection methods of the unit-4/5 index; only observation and faecal detection in a wild or semi-wild study can count as wild evidence
WILD_OBSERVATION_METHODS = {"direct_feeding_observation", "incidental_observation", "fecal_macroscopic", "fecal_histological", "fecal_detection",
                            "fecal_dna_metabarcoding", "direct_observation_and_fecal_analysis_not_separated"}
DETECTION_METHODS = WILD_OBSERVATION_METHODS | {
    "secondary_citation_method_not_verified", "secondary_reproduction_not_verified", "account_or_review_statement_method_not_given",
    "review_statement_method_not_given", "keeper_organisation_statement_method_not_given", "unreferenced_general_statement", "zoo_feeding_practice_stated",
    "husbandry_recommendation", "captive_feeding_record", "provisioned_food_observed", "resident_or_hunter_report",
    "author_list_wild_and_captive_observation_not_separated", "statement_in_article_text", "not_determinable_record_on_hold", "not_detected_by_any_method"}
# the page audit's verification levels (scripts/audit_feedipedia_sample_counts_v6.py)
LEVEL = {"matched": "mean_and_sample_count_verified", "matched_calculated": "mean_verified_calculated_value_without_sample_count",
         "mean_matched_nb_not_stored": "mean_only_verified", "excluded_nb_blank_on_page": "excluded_not_used", "excluded_but_page_prints_nb": "excluded_not_used"}


def load(name, folder=RES):
    return json.loads((folder / name).read_text(encoding="utf-8"))


def main():
    errors = []
    audit = load("feedipedia_sample_count_audit_v6.json")
    nut = {f: load(f) for f in NUTRITION}

    # 1. excluded nutrients stay excluded
    excluded = {(x["record_id"], x["nutrient_name"], x["nutrient_unit"]) for x in audit["research_values_excluded"]}
    for f, d in nut.items():
        for r in d["records"]:
            excluded |= {(r["record_id"], v["nutrient_name"], v["nutrient_unit"]) for v in r.get("values_dropped_no_sample_count_on_page") or []}
    excluded |= {(x["record_id"], x["nutrient_name"], x["nutrient_unit"]) for x in load("forage_nutrition_exclusion_audit_v5.json")["excluded_values"]}
    kept = {}
    for f, d in nut.items():
        for r in d["records"]:
            for v in r["values"]:
                k = (r["record_id"], v["nutrient_name"], v["nutrient_unit"])
                kept[k] = v
                if k in excluded:
                    errors.append("%s %s %s: an excluded value is kept again" % (f, r["record_id"], v["nutrient_name"]))
                if r["record_id"].startswith("feedipedia-") and (not isinstance(v.get("sample_count"), int) or isinstance(v.get("sample_count"), bool)):
                    errors.append("%s %s %s: kept Feedipedia value without a printed sample count (%r)" % (f, r["record_id"], v["nutrient_name"], v.get("sample_count")))
    if len(excluded) < 8:
        errors.append("fewer excluded values than the 8 found in unit 6 (%d)" % len(excluded))
    v12 = {}
    for f in NUTRITION[:2]:
        for r in nut[f]["records"]:
            for v in r["values"]:
                v12[(r["record_id"], "%s [%s, %s]" % (v["nutrient_name"], v["nutrient_unit"], v["measurement_basis"]))] = v["nutrient_value"]
    view = load("nutrient_safety_view_v3.json")
    for r in view["records"]:
        for key, val in r["values"].items():
            name, unit = re.fullmatch(r"(.+) \[([^,]+), .+\]", key).groups()
            if (r["record_id"], name, unit) in excluded:
                errors.append("nutrient view %s %s: an excluded value is shown" % (r["record_id"], key))
            if v12.get((r["record_id"], key)) != val:
                errors.append("nutrient view %s %s: not a value kept in the v1/v2 nutrition files" % (r["record_id"], key))

    # 2. public nutrition values: no sample-count verification without a sample count
    for x in audit["public_values_read_only"]:
        nb_ok = isinstance(x.get("nb_on_page"), int) and str(x.get("stored_nb")) == str(x["nb_on_page"])
        if x["status"] == "matched" and not nb_ok:
            errors.append("public %s %s %s: called matched without a stored sample count equal to a printed one" % (x["file"], x.get("plant_id"), x.get("key")))
        if x.get("stored_nb") in (None, "") and x["status"] != "mean_matched_nb_not_stored":
            errors.append("public %s %s %s: no stored sample count, status must stay mean_matched_nb_not_stored" % (x["file"], x.get("plant_id"), x.get("key")))
    pub = load("plant_nutrition_reference_v1.json", ROOT / "data")
    for r in pub["records"]:
        if re.search(r"sample.count|\bNb\b|\bn ?=", str(r.get("source_verification") or ""), re.I):
            errors.append("public %s: verification text claims a sample count the file does not store" % r["reference_id"])

    # 3. nutrition values are not feeding-safety judgements
    for f, d in nut.items():
        if "not a statement that the plant is safe" not in d["grade_policy"]:
            errors.append("%s: grade policy wording lost" % f)
        for r in d["records"]:
            if r.get("feeding_grade") is not None or r.get("feeding_verdict_use") is not False:
                errors.append("%s %s: nutrition record carries a feeding grade or verdict use" % (f, r["record_id"]))
            for k in list(r) + [k for v in r["values"] for k in v]:
                if SAFETY_WORDS.search(k) and k not in ("feeding_grade", "feeding_verdict_use"):
                    errors.append("%s %s: safety field %s in a nutrition record" % (f, r["record_id"], k))
    if "not a safety statement" not in view["note"] or "not a statement that the plant is safe" not in view["grade_policy"]:
        errors.append("nutrient view: 'not a safety statement' wording lost")
    for r in view["records"]:
        if any(SAFETY_WORDS.search(k) for k in r):
            errors.append("nutrient view %s: carries a safety field" % r["record_id"])
    hazard_ids = []
    for f in ("plant_hazard_statements_v3.json", "plant_hazard_statements_v4.json"):
        for h in load(f)["statements"]:
            hazard_ids.append(h["hazard_id"])
            if not h.get("what_it_does_not_establish") or not isinstance(h.get("tested_in_tortoises_by_this_source"), bool) or "feeding_grade" in h:
                errors.append("%s %s: hazard statement must say what it does not establish and carry no grade" % (f, h["hazard_id"]))
    for r in pub["records"]:
        if r.get("feeding_verdict_use") is not False:
            errors.append("public %s: nutrition record marked for use in a feeding verdict" % r["reference_id"])
    if "never determines" not in str(pub.get("display_policy", {}).get("safety")):
        errors.append("public nutrition file: safety display policy missing")

    # 4. consistency across units
    sources, reg = {}, {}
    for i in UNITS:
        for s in load("global_evidence_sources_v%d.json" % i)["sources"]:
            if s["source_id"] in sources:
                errors.append("source id %s repeats (unit %d)" % (s["source_id"], i))
            sources[s["source_id"]] = s
    for i in range(1, 5):
        d = load("tortoise_species_registry_v%d.json" % i)
        for s in d.get("species", []) + d.get("species_added", []):
            if s["tortoise_key"] in reg and reg[s["tortoise_key"]]["scientific_name"] != s["scientific_name"]:
                errors.append("registry key %s has two scientific names" % s["tortoise_key"])
            reg[s["tortoise_key"]] = s
        for g in d.get("groups_not_species_specific", []):
            reg.setdefault(g.get("tortoise_key") or g.get("key"), {"scientific_name": g.get("scientific_name") or g.get("name"), "group": True})
    ko_names = {}
    for k, s in reg.items():
        if s.get("common_name_ko"):
            ko_names.setdefault(s["common_name_ko"], set()).add(s["scientific_name"])
    errors += ["registry: Korean name %s used for %s" % (n, sorted(v)) for n, v in ko_names.items() if len(v) > 1]
    ev, labels = {}, {}
    for i in UNITS:
        for e in load("tortoise_plant_evidence_v%d.json" % i)["records"]:
            eid = e["evidence_id"]
            if eid in ev:
                errors.append("evidence id %s repeats (unit %d)" % (eid, i))
            ev[eid] = e
            s = sources.get(e["source_id"])
            if not s:
                errors.append("%s: unknown source %s" % (eid, e["source_id"]))
            elif e["source_url"] != s["url"] or (e.get("source_language") and s.get("language") and e["source_language"] != s["language"]) \
                    or e["verification_status"] not in (s["verification_status"], DOWNGRADED_STATUS.get(e["evidence_directness"])):
                errors.append("%s: source URL, language or status differs from source %s" % (eid, e["source_id"]))
            t = reg.get(e["tortoise_key"])
            if not t:
                errors.append("%s: tortoise key %s not in a registry" % (eid, e["tortoise_key"]))
            elif not t.get("group") and t["scientific_name"] != e["tortoise_scientific_name"]:
                errors.append("%s: tortoise name %s differs from the registry (%s)" % (eid, e["tortoise_scientific_name"], t["scientific_name"]))
            if e.get("plant_accepted_name") and not NAME.fullmatch(e["plant_accepted_name"]):
                errors.append("%s: accepted plant name %r is not a well-formed name" % (eid, e["plant_accepted_name"]))
            if not (e.get("plant_name_as_printed") or "").strip() or not (e.get("plant_part") or "").strip():
                errors.append("%s: printed plant name or plant part empty" % eid)
            if e.get("applies_to_other_tortoise_species") != "not established by this source":
                errors.append("%s: claims to apply to other tortoise species" % eid)
            if e.get("feeding_grade") is not None:
                errors.append("%s: research evidence carries a feeding grade" % eid)
            for code in ("evidence_class", "evidence_tier"):
                if e.get(code + "_ko"):
                    labels.setdefault((code, e[code]), set()).add(e[code + "_ko"])
    for (code, en), kos in labels.items():
        if len(kos) > 1:
            errors.append("%s %s has Korean labels %s" % (code, en, sorted(kos)))
    back = {}
    for (code, en), kos in labels.items():
        for ko in kos:
            back.setdefault((code, ko), set()).add(en)
    errors += ["%s Korean label %s used for %s" % (c, ko, sorted(v)) for (c, ko), v in back.items() if len(v) > 1]
    index = load("evidence_index_v5.json")["records"]
    if sorted(x["evidence_id"] for x in index) != sorted(ev):
        errors.append("unit-5 index does not hold every evidence record exactly once")
    for x in index:
        e = ev.get(x["evidence_id"])
        if e and [x["tortoise_key"], x["plant_name_as_printed"], x["plant_part"], x["wild_or_captive"], x["source_id"]] != [
                e["tortoise_key"], e["plant_name_as_printed"], e["plant_part"], e["wild_or_captive"], e["source_id"]]:
            errors.append("unit-5 index %s differs from its unit record" % x["evidence_id"])
    # 5. kinds of evidence stay apart: wild observation, captive animal, husbandry guideline, faecal/DNA detection, nutrient analysis
    for x in index:
        iid, methods = x["evidence_id"], set(x["detection_methods"])
        if not methods or not methods <= DETECTION_METHODS:
            errors.append("unit-5 index %s: detection method missing or unknown %s" % (iid, sorted(methods - DETECTION_METHODS)))
        if x["counts_as_independent_positive_wild_observation"] and (
                x["wild_or_captive"] not in ("wild", "semi_wild") or x["on_hold"] or x["is_negative_record"] or x["superseded_by"]
                or x["evidence_tier"] not in ("1_wild_feeding_study_read", "2_semi_wild_feeding_study_read") or x["wild_statement_not_an_observation"]
                or not methods & WILD_OBSERVATION_METHODS or x["evidence_directness"] != "primary_study_read"):
            errors.append("unit-5 index %s: counted as an independent wild observation but is %s / %s / %s" % (iid, x["wild_or_captive"], x["evidence_tier"], sorted(methods)))
        if x["counts_as_captive_feeding_record"] and (x["wild_or_captive"] != "captive" or x["counts_as_independent_positive_wild_observation"]):
            errors.append("unit-5 index %s: captive feeding record must be a captive animal and not a wild observation" % iid)
        if x["wild_or_captive"] not in ("wild", "semi_wild") and x["counts_as_independent_positive_wild_observation"]:
            errors.append("unit-5 index %s: a captive or previously captive animal counted as wild" % iid)
        if x["species_specific"] != (x["tortoise_key"] in reg and not reg[x["tortoise_key"]].get("group")) or not x.get("tortoise"):
            errors.append("unit-5 index %s: species_specific flag does not follow the tortoise key %s" % (iid, x["tortoise_key"]))
    lam = next((x for x in index if x["evidence_id"] == "lambert_1993-01"), None)
    if not lam or lam["counts_as_independent_positive_wild_observation"] or "previously captive" not in (lam.get("animal_history_note") or "") or lam["wild_or_captive"] == "wild":
        errors.append("lambert_1993-01: must stay a previously captive animal, never an independent wild observation")
    # a tier names the animal's setting, so it has to agree with wild_or_captive (lambert_1993-01 kept the wild tier after it was narrowed)
    tier_status = {"1_wild_feeding_study_read": "wild", "2_semi_wild_feeding_study_read": "semi_wild",
                   "2b_previously_captive_animal_field_observation_read": "previously captive; temporarily free-ranging"}
    tiers = {}
    for name in ("evidence_index_v4.json", "evidence_index_v5.json"):
        for x in load(name)["records"]:
            tiers[x["evidence_id"]] = x["evidence_tier"]
            if x["evidence_tier"] in tier_status and x["wild_or_captive"] != tier_status[x["evidence_tier"]]:
                errors.append("%s %s: tier %s but the animal is %r" % (name, x["evidence_id"], x["evidence_tier"], x["wild_or_captive"]))
    for name in ("plant_candidates_v3.json", "plant_candidates_v4.json"):
        for c in load(name)["candidates"]:
            if c.get("best_evidence_tier") == "1_wild_feeding_study_read" and not any(tiers.get(i) == "1_wild_feeding_study_read" for i in c["evidence_ids"]):
                errors.append("%s %s: best tier is a wild feeding study but no record of it is" % (name, c["candidate_key"]))
    # reviewed unit-2 corrections stay in the evidence file the unit-2 build writes
    ev2 = {e["evidence_id"]: e for e in load("tortoise_plant_evidence_v2.json")["records"]}
    for c in load("record_corrections_v2_editorial.json")["corrections"]:
        if ev2[c["evidence_id"]].get(c["field"]) != c["corrected_value"]:
            errors.append("%s %s: reviewed correction (%s) is not in tortoise_plant_evidence_v2.json" % (c["evidence_id"], c["field"], c["commit"]))
    # summary counts follow the nutrition files they describe
    s2 = load("research_layer_summary_v2.json")["summary"]
    for key, f in (("unit_1", NUTRITION[0]), ("unit_2_added", NUTRITION[1])):
        n = sum(len(r["values"]) for r in nut[f]["records"])
        if s2[key]["nutrition_values"] != n:
            errors.append("research_layer_summary_v2 %s: %d nutrition values, %s keeps %d" % (key, s2[key]["nutrition_values"], f, n))
    for f, d in nut.items():
        for r in d["records"]:
            if set(r) & {"tortoise_key", "tortoise_scientific_name", "detection_methods", "evidence_tier", "wild_or_captive"} or r["record_id"] in ev:
                errors.append("%s %s: a nutrient analysis carries tortoise-evidence fields or an evidence id" % (f, r["record_id"]))
    # 6. mean-only and mean-plus-sample-count verification stay distinguishable
    for part in ("research_values", "research_values_excluded", "public_values_read_only"):
        for x in audit[part]:
            want = LEVEL.get(x["status"], "not_verified")
            if x.get("verification_level") != want:
                errors.append("audit %s %s %s: verification_level %r, expected %r" % (part, x.get("record_id") or x.get("plant_id"), x.get("nutrient_name") or x.get("key"), x.get("verification_level"), want))
            if want == "mean_and_sample_count_verified" and not isinstance(x.get("nb_on_page"), int):
                errors.append("audit %s %s: sample count called verified without a printed one" % (part, x.get("record_id") or x.get("plant_id")))

    nids = [r["record_id"] for d in nut.values() for r in d["records"]]
    if len(set(nids)) != len(nids):
        errors.append("a nutrition record id repeats across units 1, 2 and 5")
    if len(set(hazard_ids)) != len(hazard_ids):
        errors.append("a hazard id repeats across units 3 and 4")

    report(errors, "research layer integration QA ok: %d evidence records, %d sources, %d tortoise keys, %d kept nutrition values, %d excluded values not restored, "
           "%d public values (%d with a compared sample count), %d hazard statements, %d Korean labels"
           % (len(ev), len(sources), len(reg), len(kept), len(excluded), len(audit["public_values_read_only"]),
              sum(1 for x in audit["public_values_read_only"] if x["status"] == "matched"), len(hazard_ids), sum(len(v) for v in labels.values())))


def report(errors, ok):
    if errors:
        print("research layer integration QA failed (%d):" % len(errors))
        for e in errors[:80]:
            print(" -", e)
        sys.exit(1)
    print(ok)


if __name__ == "__main__":
    main()
