#!/usr/bin/env python3
"""Offline checks for the unit-2 research files in data/research (they extend the v1 files, which stay unchanged).

Fails when
  * a file does not parse, a record lacks a required field, or an ID repeats within unit 2 or collides with unit 1,
  * a unit-2 source repeats a unit-1 source URL, or a record repeats another record of the same source,
  * a built record differs from the hand transcription (name as printed, page, tortoise, quantity, nutrient value),
  * evidence directness is overstated: 'primary_study_read' on a record whose source cites another publication, on a
    source not read in full, or on a review document; or a unit-1 record marked as checked without a read primary source,
  * a plant name gets an accepted name without passing the taxonomy check, or the queried name is more than a
    typographic variant of the printed name,
  * wild, semi-wild and captive records or the evidence classes are mixed up, or a plant part / preparation state is missing,
  * a negative (avoided / rejected) record of the transcription is missing or not flagged,
  * any record carries a feeding grade,
  * a nutrient value has an unknown unit or basis, a calculated index, a livestock digestibility or energy value,
    or a different-species table is linked to a candidate as if it were that plant's value,
  * the cumulative candidate list drops a unit-1 candidate or evidence link, repeats an accepted name, or links a
    plant ID whose scientific name is a different species,
  * the stored summary differs from a recount.

It reads data/plants.json and the v1 research files only to check links. It never writes.
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "data/research"
V1 = ["global_plant_evidence_transcription_v1.json", "global_evidence_sources_v1.json", "tortoise_species_registry_v1.json",
      "tortoise_plant_evidence_v1.json", "plant_candidates_v1.json", "forage_nutrition_research_v1.json"]
V2 = ["global_plant_evidence_transcription_v2.json", "forage_table_selection_v2.json", "global_evidence_sources_v2.json",
      "tortoise_species_registry_v2.json", "tortoise_plant_evidence_v2.json", "primary_verification_ledger_v2.json",
      "plant_candidates_v2.json", "forage_nutrition_research_v2.json", "research_layer_summary_v2.json"]
EVIDENCE_REQUIRED = ["evidence_id", "source_id", "source_url", "source_language", "source_page", "tortoise_key", "tortoise_scientific_name",
                     "plant_name_as_printed", "plant_name_queried", "plant_name_check", "plant_part", "preparation_state", "wild_or_captive",
                     "locality", "observed_consumption", "study_method", "evidence_class", "evidence_type", "evidence_directness", "limitations",
                     "verification_status"]
STUDY_TYPES = {"peer_reviewed_field_study", "peer_reviewed_captive_trial", "university_thesis_field_study"}
STATUS = {"peer_reviewed_field_study": "verified_primary_source", "peer_reviewed_captive_trial": "verified_primary_source",
          "university_thesis_field_study": "verified_primary_source_thesis", "government_conservation_plan": "verified_review_document"}
CLASSES = {"wild": {"wild_feeding_study", "local_knowledge", "conservation_plan_review", "community_provisioning"}, "semi_wild": {"semi_wild_feeding_study"},
           "captive": {"captive_feeding_trial", "husbandry_practice"}}
OK_NAME = ("accepted", "synonym_of_accepted_name", "genus_kept_as_printed_backbone_status_synonym",
           "genus_kept_as_printed_backbone_status_doubtful", "exact_match_status_doubtful")
UNITS = {("% as fed", "as fed"), ("% DM", "dry matter"), ("g/kg DM", "dry matter"), ("mg/kg DM", "dry matter")}
LEDGER_STATUS = {"confirmed_in_primary", "confirmed_with_difference", "primary_read_in_unit_1", "secondary_citation_primary_not_read",
                 "statement_of_the_source_no_primary_cited", "not_in_the_cited_source_read_other_cited_sources_unread"}


def letters(name):
    s = re.sub(r"\bssp\b", "subsp", name.lower())
    s = re.sub(r"\s+(sp|spp)\.?$", "", s)
    return re.sub(r"[^a-z]", "", s)


def main():
    errors, docs = [], {}
    for f in V1 + V2:
        try:
            docs[f] = json.loads((RES / f).read_text(encoding="utf-8"))
        except Exception as e:  # noqa: BLE001
            errors.append("%s: %s" % (f, e))
    if errors:
        report(errors)
    tr = docs["global_plant_evidence_transcription_v2.json"]
    plants = {p["id"]: p for p in json.loads((ROOT / "data/plants.json").read_text(encoding="utf-8"))}
    ev1 = docs["tortoise_plant_evidence_v1.json"]["records"]
    src1 = docs["global_evidence_sources_v1.json"]
    tortoises = {t["tortoise_key"]: t["scientific_name"] for t in docs["tortoise_species_registry_v1.json"]["species"]}
    for t in docs["tortoise_species_registry_v2.json"]["species_added"]:
        if t["tortoise_key"] in tortoises or t["scientific_name"] in tortoises.values():
            errors.append("tortoise %s is already in the unit-1 registry" % t["scientific_name"])
        if t["name_check"] != "accepted":
            errors.append("tortoise %s: name check is %s" % (t["scientific_name"], t["name_check"]))
        tortoises[t["tortoise_key"]] = t["scientific_name"]

    # sources
    slist = docs["global_evidence_sources_v2.json"]["sources"]
    sources = {s["source_id"]: s for s in slist}
    if len(sources) != len(slist) or list(sources) != list(tr["sources"]):
        errors.append("unit-2 sources do not match the transcription")
    old_urls = {s["url"] for s in src1["sources"]} | {s["url"] for s in src1["already_in_repository"]}
    old_ids = {s["source_id"] for s in src1["sources"]}
    for s in slist:
        sid = s["source_id"]
        if sid in old_ids:
            errors.append("source %s: ID already used in unit 1" % sid)
        if s["url"] in old_urls:
            errors.append("source %s: URL already recorded as a unit-1 source" % sid)
        if not str(s.get("url") or "").startswith("https://"):
            errors.append("source %s: no https URL" % sid)
        if not re.fullmatch(r"[a-z]{2}", s.get("language") or ""):
            errors.append("source %s: language code missing" % sid)
        if s["source_type"] not in STATUS or s["verification_status"] != STATUS[s["source_type"]]:
            errors.append("source %s: verification_status does not follow from its source_type" % sid)
        if s["access"] != "full_text_read":
            errors.append("source %s: unit-2 sources must have been read in full (access is %s)" % (sid, s["access"]))
        for k in ("citation", "method", "what_was_read", "study_country", "evidence_class"):
            if not s.get(k):
                errors.append("source %s: %s missing" % (sid, k))
    urls = [s["url"] for s in slist]
    if len(set(urls)) != len(urls):
        errors.append("two unit-2 sources share a URL")
    for h in docs["global_evidence_sources_v2.json"]["on_hold"] + docs["global_evidence_sources_v2.json"]["seed_mixtures_on_hold"]:
        if not h.get("reason"):
            errors.append("hold %s: reason missing" % (h.get("id") or h.get("name")))
        if h.get("id") in sources:
            errors.append("hold %s is also listed as a read source" % h["id"])

    # evidence
    evidence = docs["tortoise_plant_evidence_v2.json"]["records"]
    ids = [e["evidence_id"] for e in evidence]
    if len(set(ids)) != len(ids) or set(ids) & {e["evidence_id"] for e in ev1}:
        errors.append("evidence_id repeats within unit 2 or collides with unit 1")
    expected = [("%s-%02d" % (sid, i), row) for sid, s in tr["sources"].items() for i, row in enumerate(s["records"], 1)]
    if [x[0] for x in expected] != ids:
        errors.append("evidence records do not match the transcription (count or order)")
    rows = dict(expected)
    seen = set()
    for e in evidence:
        eid = e["evidence_id"]
        for k in EVIDENCE_REQUIRED:
            if e.get(k) in (None, ""):
                errors.append("%s: %s missing" % (eid, k))
        s = sources.get(e["source_id"])
        if not s:
            errors.append("%s: unknown source" % eid)
            continue
        if e["verification_status"] != s["verification_status"] or e["source_url"] != s["url"] or e["source_language"] != s["language"]:
            errors.append("%s: status, URL or language differs from its source" % eid)
        if tortoises.get(e["tortoise_key"]) != e["tortoise_scientific_name"]:
            errors.append("%s: tortoise taxon not in a registry" % eid)
        if e.get("feeding_grade") is not None:
            errors.append("%s: research records must not carry a feeding grade" % eid)
        row = rows.get(eid)
        if row:
            if row[1] != e["plant_name_as_printed"] or row[9] != e["source_page"] or row[0] != e["tortoise_key"] or row[6] != e["quantity_as_reported"] \
                    or row[2] != e["plant_part"] or row[4] != e["wild_or_captive"] or row[7] != e["locality"]:
                errors.append("%s: differs from the transcription" % eid)
            if bool(re.search(r"avoid|reject", row[5])) != e["is_negative_record"]:
                errors.append("%s: negative-record flag does not follow the transcribed consumption statement" % eid)
            cited = row[8]
            want = ("reported_in_source_primary_not_read" if cited else "statement_of_the_source_read" if s["source_type"] == "government_conservation_plan" else
                    "local_report_recorded_in_primary_study_read" if row[10] == 6 else "primary_study_read")
            if (row[10] == 7) != (e["evidence_class"] == "community_provisioning") or (row[10] == 5) != (e["evidence_class"] == "husbandry_practice"):
                errors.append("%s: evidence_class does not follow the transcribed evidence type" % eid)
            if e["evidence_directness"] != want:
                errors.append("%s: evidence_directness %s, expected %s" % (eid, e["evidence_directness"], want))
        if e["evidence_directness"] == "primary_study_read" and (s["source_type"] not in STUDY_TYPES or s["access"] != "full_text_read" or e["primary_reference_cited_by_source"]):
            errors.append("%s: marked primary_study_read without a primary study read in full" % eid)
        if e["wild_or_captive"] not in CLASSES or e["evidence_class"] not in CLASSES.get(e["wild_or_captive"], ()):
            errors.append("%s: wild_or_captive %r does not fit evidence_class %r" % (eid, e["wild_or_captive"], e["evidence_class"]))
        if letters(e["plant_name_queried"]) != letters(e["plant_name_as_printed"]):
            errors.append("%s: queried name %r is not a typographic variant of the printed name" % (eid, e["plant_name_queried"]))
        if e["plant_accepted_name"] and e["plant_name_check"] not in OK_NAME:
            errors.append("%s: accepted name given although the name check is %s" % (eid, e["plant_name_check"]))
        if e["plant_name_check"] in OK_NAME and not e["plant_accepted_name"]:
            errors.append("%s: name check passed but no accepted name" % eid)
        if e["plant_name_check"] == "accepted" and e["plant_rank_named_by_source"] == "species":
            m = re.match(r"[A-Z][a-z]+ [a-z-]+", e["plant_name_queried"])
            if not m or m.group(0) != e["plant_accepted_name"]:
                errors.append("%s: accepted name differs from the printed name without a synonym flag" % eid)
        if e["plant_name_check"].endswith("needs_review") and e["plant_name_check"].startswith("homonyms") and not e.get("backbone_homonyms"):
            errors.append("%s: homonym flag without the list of homonyms" % eid)
        key = (e["source_id"], e["tortoise_key"], e["plant_name_as_printed"], e["locality"], e["plant_part"], e["preparation_state"], e["wild_or_captive"])
        if key in seen:
            errors.append("%s: duplicate of another record from the same source" % eid)
        seen.add(key)
    for sid, s in tr["sources"].items():
        want = sum(bool(re.search(r"avoid|reject", r[5])) for r in s["records"])
        got = sum(e["is_negative_record"] for e in evidence if e["source_id"] == sid)
        if want != got:
            errors.append("source %s: %d negative records transcribed, %d in the evidence file" % (sid, want, got))

    # ledger of unit-1 records
    ledger = docs["primary_verification_ledger_v2.json"]["records"]
    by_id2 = {e["evidence_id"]: e for e in evidence}
    by_id1 = {e["evidence_id"]: e for e in ev1}
    if [r["v1_evidence_id"] for r in ledger] != [e["evidence_id"] for e in ev1]:
        errors.append("ledger: must hold exactly one row per unit-1 evidence record, in order")
    declared = {x["v1_evidence_id"]: x for x in tr["primary_verification_of_v1_records"]}
    for r in ledger:
        lid, st = r["v1_evidence_id"], r["status_after_unit_2"]
        e1 = by_id1.get(lid)
        if st not in LEDGER_STATUS or not e1:
            errors.append("ledger %s: unknown status or record" % lid)
            continue
        if st.startswith("confirmed"):
            s = sources.get(r.get("primary_source_id"))
            e2 = by_id2.get(r.get("v2_evidence_id"))
            if lid not in declared or not s or s["source_type"] not in STUDY_TYPES or s["access"] != "full_text_read":
                errors.append("ledger %s: marked %s without a primary source read in full" % (lid, st))
            elif not e2 or e2["source_id"] != r["primary_source_id"] or e2["tortoise_key"] != e1["tortoise_key"]:
                errors.append("ledger %s: no matching unit-2 record for the same tortoise in %s" % (lid, r["primary_source_id"]))
            if st == "confirmed_with_difference" and not r.get("note"):
                errors.append("ledger %s: a difference must be described" % lid)
        elif st == "not_in_the_cited_source_read_other_cited_sources_unread":
            s = sources.get(r.get("primary_source_id"))
            if lid not in declared or not s or s["access"] != "full_text_read" or r.get("v2_evidence_id") or not r.get("note"):
                errors.append("ledger %s: 'not in the cited source' needs a source read in full, a note and no unit-2 record" % lid)
            if any(e2["source_id"] == r["primary_source_id"] and e2["tortoise_key"] == e1["tortoise_key"] and e2["plant_name_as_printed"] == e1["plant_name_as_printed"] for e2 in evidence):
                errors.append("ledger %s: the plant is recorded from that source after all" % lid)
        elif lid in declared:
            errors.append("ledger %s: declared as checked in the transcription but status is %s" % (lid, st))
        if st == "primary_read_in_unit_1" and e1["evidence_directness"] != "primary_study_read":
            errors.append("ledger %s: unit 1 did not read a primary study for this record" % lid)
        if st == "secondary_citation_primary_not_read" and (r.get("primary_source_id") or e1["evidence_directness"] != "reported_in_account_primary_not_read"):
            errors.append("ledger %s: inconsistent secondary-citation row" % lid)
        for pid in r["independent_primary_records_same_tortoise_and_plant"]:
            p = by_id2.get(pid) or by_id1.get(pid)
            if not p or p["evidence_directness"] != "primary_study_read" or p["tortoise_key"] != e1["tortoise_key"] or p["source_id"] == e1["source_id"]:
                errors.append("ledger %s: %s is not an independent primary record for the same tortoise" % (lid, pid))

    # cumulative candidates
    cands = docs["plant_candidates_v2.json"]["candidates"]
    cmap = {c["candidate_key"]: c for c in cands}
    if len(cmap) != len(cands):
        errors.append("duplicate candidate_key")
    accepted = Counter(c["accepted_name"] for c in cands if c["accepted_name"])
    for n, k in accepted.items():
        if k > 1:
            errors.append("accepted name %s appears as more than one candidate" % n)
    for c1 in docs["plant_candidates_v1.json"]["candidates"]:
        c2 = cmap.get(c1["candidate_key"])
        if not c2:
            errors.append("unit-1 candidate %s is missing from the cumulative list" % c1["candidate_key"])
        elif not set(c1["evidence_ids"]) <= set(c2["evidence_ids"]) or not set(c1["seed_mixture_ids"]) <= set(c2["seed_mixture_ids"]) \
                or not set(c1["names_as_printed"]) <= set(c2["names_as_printed"]) or not set(c1["forage_nutrition_record_ids"]) <= set(c2["forage_nutrition_record_ids"]):
            errors.append("candidate %s lost a unit-1 link" % c1["candidate_key"])
    nut = docs["forage_nutrition_research_v2.json"]["records"]
    nut_ids = {r["record_id"] for r in nut} | {r["record_id"] for r in docs["forage_nutrition_research_v1.json"]["records"]}
    linked, linked_nut = set(), set()
    for c in cands:
        if c.get("feeding_grade") is not None:
            errors.append("candidate %s carries a feeding grade" % c["candidate_key"])
        for eid in c["evidence_ids"]:
            if eid not in by_id1 and eid not in by_id2:
                errors.append("candidate %s: unknown evidence %s" % (c["candidate_key"], eid))
            linked.add(eid)
        for pid in c["existing_plant_ids"] + c["existing_genus_level_plant_ids"]:
            if pid not in plants:
                errors.append("candidate %s: unknown plant id %s" % (c["candidate_key"], pid))
        for pid in c["existing_plant_ids"]:
            if pid in plants and plants[pid]["scientific"].split()[0] != c["accepted_name"].split()[0] and not c["name_check"].startswith("synonym"):
                errors.append("candidate %s linked to %s (%s)" % (c["candidate_key"], pid, plants[pid]["scientific"]))
        if c["database_status"] == "not_in_database" and not c["accepted_name"]:
            errors.append("candidate %s: unresolved name listed as a new candidate" % c["candidate_key"])
        for rid in c["forage_nutrition_record_ids"]:
            if rid not in nut_ids:
                errors.append("candidate %s points to missing nutrition record %s" % (c["candidate_key"], rid))
            linked_nut.add(rid)
    for eid in list(by_id1) + ids:
        if eid not in linked:
            errors.append("%s: not linked to any candidate" % eid)

    # nutrition
    rids = [r["record_id"] for r in nut]
    if len(set(rids)) != len(rids) or set(rids) & {r["record_id"] for r in docs["forage_nutrition_research_v1.json"]["records"]}:
        errors.append("nutrition record_id repeats within unit 2 or collides with unit 1")
    hand = {t["table_id"]: t for t in tr["nutrient_tables"]}
    selected = {str(t["node"]): t for t in docs["forage_table_selection_v2.json"]["tables"]}
    if len(hand) != len(tr["nutrient_tables"]):
        errors.append("duplicate table_id in the transcribed nutrient tables")
    for tid in hand:
        if tid not in rids:
            errors.append("transcribed nutrient table %s is missing from the nutrition file" % tid)
    for r in nut:
        rid = r["record_id"]
        if r["preparation_state"] not in ("fresh", "hay", "dried", "crop_residue"):
            errors.append("%s: preparation_state %r" % (rid, r["preparation_state"]))
        if r.get("feeding_verdict_use") is not False or r.get("feeding_grade") is not None:
            errors.append("%s: nutrition must not feed verdicts" % rid)
        if not r["analyzed_taxon"] or not r["analyzed_part"] or not r["use_limits"]:
            errors.append("%s: analyzed taxon, part or use limits missing" % rid)
        if r["source_kind"] == "study_table_transcribed_by_hand":
            t = hand.get(rid)
            if not t or r["source_id"] not in sources or t["analyzed_taxon"] != r["analyzed_taxon"] or t["analyzed_part"] != r["analyzed_part"] \
                    or [[v["nutrient_name"], v["nutrient_value"], v["nutrient_unit"], v["measurement_basis"], v["sample_count"]] for v in r["values"]] != t["values"]:
                errors.append("%s: differs from the transcribed table" % rid)
        elif r["source_kind"] == "compiled_feed_table_parsed":
            t = selected.get(r["source_id"])
            if not t or not r["source_url"].endswith("/node/" + r["source_id"]) or t["match"] != r["match_to_candidate"]:
                errors.append("%s: table not in the selection file, URL mismatch or match type changed" % rid)
        else:
            errors.append("%s: unknown source_kind" % rid)
        same = r["match_to_candidate"] in ("same_species", "same_taxon_name_as_an_evidence_record")
        if not same and (rid in linked_nut or not r.get("reference_for_taxon") or "Different species" not in r["use_limits"]):
            errors.append("%s: a different-species table must stay reference only, name the taxon it is a reference for, and state the limit" % rid)
        names = [v["nutrient_name"] for v in r["values"]]
        if len(set(names)) != len(names) or not names:
            errors.append("%s: empty or repeated nutrient" % rid)
        for v in r["values"]:
            pair = (v["nutrient_unit"], v["measurement_basis"])
            if pair not in UNITS and not (pair == ("%", "not stated in the table") and r.get("basis_note")):
                errors.append("%s: %s unit/basis %s / %s" % (rid, v["nutrient_name"], v["nutrient_unit"], v["measurement_basis"]))
            if not isinstance(v["nutrient_value"], (int, float)) or isinstance(v["nutrient_value"], bool) or v["nutrient_value"] < 0:
                errors.append("%s: %s value %r" % (rid, v["nutrient_name"], v["nutrient_value"]))
            elif v["nutrient_unit"].startswith("%") and v["nutrient_value"] > 100:
                errors.append("%s: %s above 100%%" % (rid, v["nutrient_name"]))
            if not isinstance(v["sample_count"], int) and not (v["sample_count"] is None and r.get("sample_count_note")):
                errors.append("%s: %s has no sample count and no note explaining why" % (rid, v["nutrient_name"]))
            if re.search(r"ruminant|digestib|energy|\bde\b|\bme\b|pig|rabbit|poultry|\bpep\b|index|excretion", v["nutrient_name"]):
                errors.append("%s: calculated index or livestock value %s" % (rid, v["nutrient_name"]))
        dm = [v["nutrient_value"] for v in r["values"] if v["nutrient_name"] == "dry matter" and v["nutrient_unit"] == "% as fed"]
        fresh_parts = sum(v["nutrient_value"] for v in r["values"] if v["nutrient_unit"] == "%" and v["nutrient_name"] != "dry matter")
        if dm and fresh_parts > dm[0] + 0.01:
            errors.append("%s: components with an unstated basis sum above dry matter, so they cannot be fresh-matter values" % rid)

    # summary recount
    sm = docs["research_layer_summary_v2.json"]["summary"]
    recount = {"unit2 evidence": (sm["unit_2_added"]["evidence"]["records"], len(evidence)),
               "unit1 evidence": (sm["unit_1"]["evidence"]["records"], len(ev1)),
               "cumulative evidence": (sm["cumulative"]["evidence_records"], len(ev1) + len(evidence)),
               "cumulative names": (sm["cumulative"]["candidates"]["plant_names"], len(cands)),
               "new candidates": (sm["cumulative"]["candidates"]["new_candidates_not_in_database"], sum(c["database_status"] == "not_in_database" for c in cands)),
               "primary read": (sm["cumulative"]["primary_study_read_records"], sum(e["evidence_directness"] == "primary_study_read" for e in ev1 + evidence)),
               "nutrition": (sm["unit_2_added"]["nutrition_records"], len(nut)),
               "ledger": (sum(sm["unit_1_records_after_primary_check"].values()), len(ev1)),
               "ledger confirmed": (sm["unit_1_records_after_primary_check"].get("confirmed_in_primary", 0) + sm["unit_1_records_after_primary_check"].get("confirmed_with_difference", 0),
                                    sum(r["status_after_unit_2"].startswith("confirmed") for r in ledger))}
    for k, (stored, counted) in recount.items():
        if stored != counted:
            errors.append("summary: %s is stored as %s but recounts to %s" % (k, stored, counted))

    report(errors, "research layer unit-2 QA ok: %d sources, %d evidence records (%d primary study read), %d unit-1 records checked against their primary, %d candidates cumulative, %d nutrition records"
           % (len(slist), len(evidence), sum(e["evidence_directness"] == "primary_study_read" for e in evidence),
              sum(r["status_after_unit_2"].startswith("confirmed") for r in ledger), len(cands), len(nut)))


def report(errors, ok=None):
    if errors:
        print("research layer unit-2 QA failed (%d):" % len(errors))
        for e in errors[:80]:
            print(" -", e)
        sys.exit(1)
    if ok:
        print(ok)


if __name__ == "__main__":
    main()
