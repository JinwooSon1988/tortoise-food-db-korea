#!/usr/bin/env python3
"""Offline checks for the unit-5 research files in data/research (they extend the v1-v4 files, which stay unchanged).

Fails when
  * a file does not parse, a record lacks a required field, or an ID repeats or collides with units 1-4,
  * a built record differs from the hand transcription,
  * a unit-5 source repeats a source of units 1-4 (same URL or citation) and would be counted as independent evidence,
  * detection methods are mixed up: a zoo statement labelled as a captive study record or the reverse, an unreferenced
    general statement given a study tier, or any unit-5 record labelled as a wild observation or fecal detection,
  * a common-name label or an unconfirmed name carries a scientific name,
  * a nutrient value has an unknown unit or basis, no sample count, a livestock energy or digestibility label, a silage
    table, a calcium-to-phosphorus quotient that is not flagged or does not follow from the stored values, or a
    reference-only table claims a candidate,
  * any object carries a feeding grade, or the stored summary differs from a recount.
It never writes.
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "data/research"
NEW = ["global_plant_evidence_transcription_v5.json", "global_evidence_sources_v5.json", "tortoise_plant_evidence_v5.json", "forage_nutrition_research_v5.json",
       "forage_table_selection_v5.json", "research_layer_summary_v5.json"]
OLD = ["global_evidence_sources_v%d.json" % i for i in (1, 2, 3, 4)] + ["tortoise_plant_evidence_v%d.json" % i for i in (1, 2, 3, 4)] + \
      ["plant_candidates_v4.json", "evidence_index_v4.json", "forage_nutrition_research_v1.json", "forage_nutrition_research_v2.json", "tortoise_species_registry_v1.json"]
REQUIRED = ["evidence_id", "source_id", "source_url", "source_citation", "source_page", "tortoise_key", "tortoise_scientific_name", "plant_name_as_printed", "plant_name_check",
            "plant_part", "preparation_state", "wild_or_captive", "locality", "observed_consumption", "study_method", "detection_methods", "evidence_class", "evidence_type",
            "evidence_directness", "evidence_tier", "limitations", "verification_status"]
STATUS = {"peer_reviewed_captive_study": "verified_primary_source", "zoo_information_page": "verified_zoo_statement"}
METHODS = {5: {"captive_feeding_record"}, 8: {"zoo_feeding_practice_stated", "unreferenced_general_statement"}}
TIER = {5: "3_captive_feeding_trial_read", 8: "4_institutional_husbandry_guideline"}
OK_NAME = ("accepted", "synonym_of_accepted_name", "genus_kept_as_printed_backbone_status_synonym", "genus_kept_as_printed_backbone_status_doubtful", "exact_match_status_doubtful")
UNITS = {("% as fed", "as fed"), ("% DM", "dry matter"), ("g/kg DM", "dry matter"), ("mg/kg DM", "dry matter")}
COMMON = r"common names? only|common name as printed|local name only|food group only|plant group only|unidentified|not identified|not resolved|not confirmed"


def norm(s):
    return re.sub(r"\W+", "", s.lower())[:80]


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
    for f in NEW + OLD:
        try:
            d[f] = json.loads((RES / f).read_text(encoding="utf-8"))
        except Exception as e:  # noqa: BLE001
            errors.append("%s: %s" % (f, e))
    if errors:
        report(errors)
    for f in NEW[1:]:
        grades(d[f], f, errors)
    tr = d["global_plant_evidence_transcription_v5.json"]
    old_sources = [s for i in (1, 2, 3, 4) for s in d["global_evidence_sources_v%d.json" % i]["sources"]]
    old_ids = {e["evidence_id"] for i in (1, 2, 3, 4) for e in d["tortoise_plant_evidence_v%d.json" % i]["records"]}
    tort = {t["tortoise_key"]: t["scientific_name"] for t in d["tortoise_species_registry_v1.json"]["species"]}

    sdoc = d["global_evidence_sources_v5.json"]
    sources = {s["source_id"]: s for s in sdoc["sources"]}
    if list(sources) != list(tr["sources"]) or len(sources) != len(sdoc["sources"]) or set(sources) & {s["source_id"] for s in old_sources}:
        errors.append("unit-5 sources do not match the transcription or reuse an earlier source ID")
    old_urls, old_cit = {s["url"].lower() for s in old_sources}, {norm(s["citation"]) for s in old_sources}
    for s in sdoc["sources"]:
        sid = s["source_id"]
        if s["url"].lower() in old_urls or norm(s["citation"]) in old_cit:
            errors.append("source %s: already a source in units 1-4; it must not be counted again" % sid)
        if not s["url"].startswith("https://") or STATUS.get(s["source_type"]) != s["verification_status"] or s["access"] != "full_text_read":
            errors.append("source %s: URL, status or access wrong" % sid)
        for k in ("citation", "method", "what_was_read", "language", "study_country"):
            if not s.get(k):
                errors.append("source %s: %s missing" % (sid, k))
        if s.get("year") is None and "year" not in s["what_was_read"]:
            errors.append("source %s: no year and no note saying the source gives none" % sid)

    ev = d["tortoise_plant_evidence_v5.json"]["records"]
    expected = [("%s-%02d" % (sid, i), row) for sid, s in tr["sources"].items() for i, row in enumerate(s["records"], 1)]
    ids = [e["evidence_id"] for e in ev]
    if [x[0] for x in expected] != ids or len(set(ids)) != len(ids) or set(ids) & old_ids:
        errors.append("evidence records do not match the transcription, repeat, or collide with units 1-4")
    # Zoo-page descriptions of wild diet are not verified wild feeding observations.
    zoo_wild = [e for e in ev if e["wild_or_captive"] == "wild" and e["source_id"] in {"salisbury_zoo_sulcata_page", "exmoor_zoo_sulcata_page"}]
    for e in zoo_wild:
        if e["detection_methods"] != ["unreferenced_general_statement"] or e["evidence_tier"].startswith(("1_", "2_", "3_")):
            errors.append("%s: zoo wild-diet prose must not be treated as a verified wild feeding observation" % e["evidence_id"])
    if len(zoo_wild) != 4:
        errors.append("unit-5 zoo wild-diet prose count changed: review the four unreferenced records")
    rows, seen = dict(expected), set()
    for e in ev:
        eid = e["evidence_id"]
        for k in REQUIRED:
            if e.get(k) in (None, "", []):
                errors.append("%s: %s missing" % (eid, k))
        s = sources.get(e["source_id"])
        row = rows.get(eid)
        if not s or not row:
            continue
        if [row[0], row[1], row[2], row[3], row[4], row[5], row[7], row[9], row[12]] != [e["tortoise_key"], e["plant_name_as_printed"], e["plant_part"], e["preparation_state"],
                                                                                         e["wild_or_captive"], e["observed_consumption"], e["locality"], e["source_page"], e["detection_methods"]]:
            errors.append("%s: differs from the transcription" % eid)
        if tort.get(e["tortoise_key"]) != e["tortoise_scientific_name"] or e["verification_status"] != s["verification_status"] or e["source_url"] != s["url"]:
            errors.append("%s: tortoise, status or URL inconsistent" % eid)
        typ = row[10]
        if not set(e["detection_methods"]) <= METHODS[typ] or e["evidence_tier"] != TIER[typ]:
            errors.append("%s: detection method or tier does not fit the evidence type (%s)" % (eid, e["detection_methods"]))
        if "unreferenced_general_statement" in e["detection_methods"] and e["evidence_tier"].startswith(("1_", "2_", "3_")):
            errors.append("%s: an unreferenced statement is given a study tier" % eid)
        if e["evidence_directness"] == "primary_study_read":
            errors.append("%s: no unit-5 record is a wild study read" % eid)
        if re.search(COMMON, row[11] or "") and e["plant_accepted_name"]:
            errors.append("%s: a common-name or unconfirmed label carries a scientific name" % eid)
        if e["plant_accepted_name"] and e["plant_name_check"] not in OK_NAME:
            errors.append("%s: accepted name without a passed name check" % eid)
        key = (e["source_id"], e["plant_name_as_printed"], e["plant_part"], e["preparation_state"], e["wild_or_captive"])
        if key in seen:
            errors.append("%s: duplicate record within the source" % eid)
        seen.add(key)

    nut = d["forage_nutrition_research_v5.json"]["records"]
    sel = {str(t["node"]): t for t in d["forage_table_selection_v5.json"]["tables"]}
    old_nut = {r["record_id"] for f in ("forage_nutrition_research_v1.json", "forage_nutrition_research_v2.json") for r in d[f]["records"]}
    accepted4 = {c["accepted_name"]: c["candidate_key"] for c in d["plant_candidates_v4.json"]["candidates"] if c["accepted_name"]}
    # Structural checks for Feedipedia means; not a substitute for source-page verification.
    for r in nut:
        rid = r["record_id"]
        names = set()
        vals = {}
        for v in r["values"]:
            name = v["nutrient_name"]
            if name in names:
                errors.append("%s: duplicate nutrient %s" % (rid, name))
            names.add(name)
            vals[name] = v
            if not isinstance(v["nutrient_value"], (int, float)) or isinstance(v["nutrient_value"], bool) or v["sample_count"] < 1:
                errors.append("%s: invalid nutrient value or sample count for %s" % (rid, name))
            expected_basis = "as fed" if name == "dry matter" else "dry matter"
            if v["measurement_basis"] != expected_basis:
                errors.append("%s: unexpected basis for %s" % (rid, name))
        ca, p = vals.get("calcium"), vals.get("phosphorus")
        ratio = r.get("calcium_to_phosphorus")
        if ratio and ca and p and p["nutrient_value"] > 0:
            if abs(round(ca["nutrient_value"] / p["nutrient_value"], 2) - ratio["value"]) > 0.011:
                errors.append("%s: calcium/phosphorus ratio disagrees with reported means" % rid)
    for r in nut:
        rid = r["record_id"]
        t = sel.get(r["source_id"])
        if not t or not r["source_url"].endswith("/node/" + r["source_id"]) or rid in old_nut or "silage" in r["table_title_as_printed"].lower():
            errors.append("%s: not in the selection, URL mismatch, already in units 1-2, or a silage table" % rid)
        if r["preparation_state"] not in ("fresh", "hay") or (("hay" in r["table_title_as_printed"].lower()) != (r["preparation_state"] == "hay")):
            errors.append("%s: preparation state does not follow the table title" % rid)
        if r.get("feeding_verdict_use") is not False:
            errors.append("%s: nutrition must not feed verdicts" % rid)
        same = r["match_to_candidate"] == "same_species_as_a_candidate"
        if same != (r["analyzed_taxon_accepted_name"] in accepted4) or (same and r["candidate_key"] != accepted4[r["analyzed_taxon_accepted_name"]]) or (not same and (r["candidate_key"] or "No evidence record names this species" not in r["use_limits"])):
            errors.append("%s: candidate match is wrong or a reference-only table claims a candidate" % rid)
        vals = {}
        for v in r["values"]:
            vals[(v["nutrient_name"], v["nutrient_unit"])] = v["nutrient_value"]
            if (v["nutrient_unit"], v["measurement_basis"]) not in UNITS or not isinstance(v["sample_count"], int) or not isinstance(v["nutrient_value"], (int, float)) or v["nutrient_value"] < 0 \
                    or (v["nutrient_unit"].startswith("%") and v["nutrient_value"] > 100) or re.search(r"ruminant|digestib|energy|\bde\b|\bme\b|pig|rabbit|poultry", v["nutrient_name"]):
                errors.append("%s: %s has a bad unit, basis, count, value or label" % (rid, v["nutrient_name"]))
        q = r.get("calcium_to_phosphorus")
        ca, ph = vals.get(("calcium", "g/kg DM")), vals.get(("phosphorus", "g/kg DM"))
        if (q is None) != (not (ca and ph)) or (q and (q.get("derived_by_this_layer") is not True or round(ca / ph, 2) != q["value"] or not q.get("caution"))):
            errors.append("%s: calcium-to-phosphorus quotient missing, unflagged or inconsistent" % rid)

    sm = d["research_layer_summary_v5.json"]["summary"]
    idx = d["evidence_index_v4.json"]["records"]
    seen_names = {x["plant_name_as_printed"] for x in idx} | {p for c in d["plant_candidates_v4.json"]["candidates"] for p in c["names_as_printed"]}
    for name, stored, counted in [("evidence", sm["unit_5_added"]["evidence_records"], len(ev)), ("nutrition", sm["unit_5_added"]["nutrition_records"], len(nut)),
                                  ("new names", sm["unit_5_added"]["plant_names_new_against_units_1_to_4"], sorted({e["plant_name_as_printed"] for e in ev} - seen_names)),
                                  ("methods", sm["unit_5_added"]["evidence_by_detection_method"], dict(sorted(Counter(m for e in ev for m in e["detection_methods"]).items()))),
                                  ("duplicate sources", sm["duplicate_check"]["sources_already_in_units_1_to_4"], [])]:
        if stored != counted:
            errors.append("summary: %s is stored as %s but recounts to %s" % (name, stored, counted))
    report(errors, "research layer unit-5 QA ok: %d sources, %d evidence records, %d nutrition records, no source repeated from units 1-4" % (len(sources), len(ev), len(nut)))


def report(errors, ok=None):
    if errors:
        print("research layer unit-5 QA failed (%d):" % len(errors))
        for e in errors[:80]:
            print(" -", e)
        sys.exit(1)
    if ok:
        print(ok)


if __name__ == "__main__":
    main()
