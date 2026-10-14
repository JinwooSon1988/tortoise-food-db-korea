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
