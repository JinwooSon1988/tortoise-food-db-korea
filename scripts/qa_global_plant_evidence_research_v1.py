#!/usr/bin/env python3
"""Offline checks for the research layer in data/research (global tortoise food-plant evidence).

Fails when
  * a file does not parse or a record lacks a required field,
  * an ID is duplicated, or a record points to a source, tortoise taxon, candidate or plant ID that does not exist,
  * the built evidence or seed-mixture records differ from the hand transcription (name, page or count),
  * a source that was not read in the original is marked as verified,
  * any record carries a feeding grade, or a name that failed the taxonomy check has an accepted name,
  * a nutrition value has an unknown unit, mixes as-fed and dry-matter bases, or comes from a calculated or
    livestock digestibility row,
  * the same accepted plant name appears as two candidates, or a candidate claims an existing plant ID whose
    scientific name is a different species.

It reads data/plants.json only to check links. It never writes.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "data/research"
FILES = ["global_plant_evidence_transcription_v1.json", "forage_table_selection_v1.json", "global_evidence_sources_v1.json",
         "tortoise_species_registry_v1.json", "tortoise_plant_evidence_v1.json", "enclosure_seed_mixtures_v1.json",
         "plant_candidates_v1.json", "forage_nutrition_research_v1.json"]
EVIDENCE_REQUIRED = ["evidence_id", "source_id", "source_url", "source_page", "tortoise_key", "tortoise_scientific_name", "plant_name_as_printed",
                     "plant_name_check", "plant_part", "preparation_state", "wild_or_captive", "locality", "observed_consumption", "evidence_type",
                     "evidence_directness", "limitations", "verification_status"]
STATUS = {"verified_primary_source", "verified_in_peer_reviewed_account", "verified_abstract_only", "hold_original_not_read"}
UNITS = {"% as fed": "as fed", "% DM": "dry matter", "g/kg DM": "dry matter", "mg/kg DM": "dry matter"}
OK_NAME = ("accepted", "synonym_of_accepted_name", "genus_kept_as_printed_backbone_status_synonym",
           "genus_kept_as_printed_backbone_status_doubtful", "exact_match_status_doubtful")


def main():
    errors = []
    docs = {}
    for f in FILES:
        try:
            docs[f] = json.loads((RES / f).read_text(encoding="utf-8"))
        except Exception as e:  # noqa: BLE001
            errors.append("%s: %s" % (f, e))
    if errors:
        report(errors)
    tr = docs["global_plant_evidence_transcription_v1.json"]
    plants = {p["id"]: p for p in json.loads((ROOT / "data/plants.json").read_text(encoding="utf-8"))}
    sources = {s["source_id"]: s for s in docs["global_evidence_sources_v1.json"]["sources"]}
    if len(sources) != len(docs["global_evidence_sources_v1.json"]["sources"]):
        errors.append("duplicate source_id")
    tortoises = {t["tortoise_key"]: t for t in docs["tortoise_species_registry_v1.json"]["species"]}
    for t in tortoises.values():
        if t["name_check"] != "accepted":
            errors.append("tortoise %s: name check is %s" % (t["scientific_name"], t["name_check"]))
    sci = [t["scientific_name"] for t in tortoises.values()]
    if len(set(sci)) != len(sci):
        errors.append("duplicate tortoise scientific name")
    for s in sources.values():
        if not str(s.get("url") or "").startswith("https://"):
            errors.append("source %s: no https URL" % s["source_id"])
        if s["access"] != "full_text_read" and s["verification_status"] in ("verified_primary_source", "verified_in_peer_reviewed_account"):
            errors.append("source %s: not read in full but marked %s" % (s["source_id"], s["verification_status"]))

    evidence = docs["tortoise_plant_evidence_v1.json"]["records"]
    ids = [e["evidence_id"] for e in evidence]
    if len(set(ids)) != len(ids):
        errors.append("duplicate evidence_id")
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
        if e["source_id"] not in sources:
            errors.append("%s: unknown source" % eid)
        elif e["verification_status"] != sources[e["source_id"]]["verification_status"] or e["source_url"] != sources[e["source_id"]]["url"]:
            errors.append("%s: status or URL differs from its source" % eid)
        if e["tortoise_key"] not in tortoises or tortoises[e["tortoise_key"]]["scientific_name"] != e["tortoise_scientific_name"]:
            errors.append("%s: tortoise taxon not in registry" % eid)
        if e["verification_status"] not in STATUS:
            errors.append("%s: unknown verification_status" % eid)
        if e.get("feeding_grade") is not None:
            errors.append("%s: research records must not carry a feeding grade" % eid)
        if e["wild_or_captive"] not in ("wild", "captive"):
            errors.append("%s: wild_or_captive is %r" % (eid, e["wild_or_captive"]))
        row = rows.get(eid)
        if row and (row[1] != e["plant_name_as_printed"] or row[9] != e["source_page"] or row[0] != e["tortoise_key"] or row[6] != e["quantity_as_reported"]):
            errors.append("%s: differs from the transcription" % eid)
        if e["plant_accepted_name"] and e["plant_name_check"] not in OK_NAME:
            errors.append("%s: accepted name given although the name check is %s" % (eid, e["plant_name_check"]))
        if e["plant_name_check"] == "accepted" and e["plant_rank_named_by_source"] == "species" and e["plant_accepted_name"] != e["plant_name_as_printed"]:
            errors.append("%s: accepted name differs from the printed name without a synonym flag" % eid)
        key = (e["source_id"], e["tortoise_key"], e["plant_name_as_printed"], e["locality"], e["plant_part"], e["wild_or_captive"])
        if key in seen:
            errors.append("%s: duplicate of another record from the same source" % eid)
        seen.add(key)

    cands = docs["plant_candidates_v1.json"]["candidates"]
    keys = [c["candidate_key"] for c in cands]
    if len(set(keys)) != len(keys):
        errors.append("duplicate candidate_key")
    accepted = [c["accepted_name"] for c in cands if c["accepted_name"]]
    for n in sorted({n for n in accepted if accepted.count(n) > 1}):
        errors.append("accepted name %s appears as more than one candidate" % n)
    linked = set()
    for c in cands:
        if c.get("feeding_grade") is not None:
            errors.append("candidate %s carries a feeding grade" % c["candidate_key"])
        for eid in c["evidence_ids"]:
            if eid not in rows:
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
    for eid in ids:
        if eid not in linked:
            errors.append("%s: not linked to any candidate" % eid)

    mixes = docs["enclosure_seed_mixtures_v1.json"]["mixtures"]
    mids = [m["mixture_id"] for m in mixes]
    if len(set(mids)) != len(mids) or mids != [m["mixture_id"] for m in tr["seed_mixtures"]]:
        errors.append("seed mixtures do not match the transcription")
    for m, src in zip(mixes, tr["seed_mixtures"]):
        if not m["source_url"].startswith("https://") or not m["country"]:
            errors.append("mixture %s: source_url or country missing" % m["mixture_id"])
        if [[c["scientific_name_as_printed"], c["common_name_as_printed"], c["ratio_as_printed"]] for c in m["components"]] != src["components"]:
            errors.append("mixture %s: components differ from the transcription" % m["mixture_id"])
        names = [c["scientific_name_as_printed"] or c["common_name_as_printed"] for c in m["components"]]
        if len(set(names)) != len(names):
            errors.append("mixture %s: a component is listed twice" % m["mixture_id"])
        for c in m["components"]:
            if c["ratio_as_printed"] is not None and not re.fullmatch(r"\d+(\.\d+)?%", c["ratio_as_printed"]):
                errors.append("mixture %s: ratio %r" % (m["mixture_id"], c["ratio_as_printed"]))
            if c["accepted_name"] and c["name_check"] not in OK_NAME:
                errors.append("mixture %s: %s has an accepted name without a passed name check" % (m["mixture_id"], names[0]))
        if "not evidence" not in m["safety_statement"]:
            errors.append("mixture %s: safety statement missing" % m["mixture_id"])

    nut = docs["forage_nutrition_research_v1.json"]["records"]
    selected = {str(t["node"]) for t in docs["forage_table_selection_v1.json"]["tables"]}
    rids = [r["record_id"] for r in nut]
    if len(set(rids)) != len(rids):
        errors.append("duplicate nutrition record_id")
    cand_nut = {i for c in cands for i in c["forage_nutrition_record_ids"]}
    for r in nut:
        rid = r["record_id"]
        if r["source_id"] not in selected or not r["source_url"].endswith("/node/" + r["source_id"]):
            errors.append("%s: table not in the selection file or URL mismatch" % rid)
        if r["preparation_state"] not in ("fresh", "hay", "dried", "crop_residue"):
            errors.append("%s: preparation_state %r" % (rid, r["preparation_state"]))
        if r.get("feeding_verdict_use") is not False:
            errors.append("%s: nutrition must not feed verdicts" % rid)
        if not r["analyzed_taxon"] or not r["analyzed_part"]:
            errors.append("%s: analyzed taxon or part missing" % rid)
        names = [v["nutrient_name"] for v in r["values"]]
        if len(set(names)) != len(names) or not names:
            errors.append("%s: empty or repeated nutrient" % rid)
        for v in r["values"]:
            if v["nutrient_unit"] not in UNITS or UNITS[v["nutrient_unit"]] != v["measurement_basis"]:
                errors.append("%s: %s unit/basis %s / %s" % (rid, v["nutrient_name"], v["nutrient_unit"], v["measurement_basis"]))
            if not isinstance(v["nutrient_value"], (int, float)) or isinstance(v["nutrient_value"], bool) or v["nutrient_value"] < 0:
                errors.append("%s: %s value %r" % (rid, v["nutrient_name"], v["nutrient_value"]))
            if v["nutrient_unit"] in ("% as fed", "% DM") and v["nutrient_value"] > 100:
                errors.append("%s: %s above 100%%" % (rid, v["nutrient_name"]))
            if not isinstance(v["sample_count"], int):
                errors.append("%s: %s has no sample count (calculated values are not allowed)" % (rid, v["nutrient_name"]))
            if re.search(r"ruminant|digestib|energy|\bde\b|\bme\b|pig|rabbit|poultry", v["nutrient_name"]):
                errors.append("%s: livestock digestibility or energy value %s" % (rid, v["nutrient_name"]))
    for i in cand_nut - set(rids):
        errors.append("candidate points to missing nutrition record %s" % i)

    report(errors, "research layer QA ok: %d sources, %d tortoise taxa, %d evidence records, %d candidates, %d seed mixtures, %d nutrition records"
           % (len(sources), len(tortoises), len(evidence), len(cands), len(mixes), len(nut)))


def report(errors, ok=None):
    if errors:
        print("research layer QA failed (%d):" % len(errors))
        for e in errors[:80]:
            print(" -", e)
        sys.exit(1)
    if ok:
        print(ok)


if __name__ == "__main__":
    main()
