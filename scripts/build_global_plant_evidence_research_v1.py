#!/usr/bin/env python3
"""Expand the hand transcription of global tortoise food-plant sources into research data sets.

Input   data/research/global_plant_evidence_transcription_v1.json   (names exactly as the sources print them)
        data/research/forage_table_selection_v1.json                (Feedipedia tables chosen for candidate plants)
Output  data/research/global_evidence_sources_v1.json
        data/research/tortoise_species_registry_v1.json
        data/research/tortoise_plant_evidence_v1.json
        data/research/enclosure_seed_mixtures_v1.json
        data/research/plant_candidates_v1.json
        data/research/forage_nutrition_research_v1.json

Every plant and tortoise name is checked against the GBIF backbone (api.gbif.org/v1/species/match). Fuzzy and
higher-rank matches are never accepted silently: they are kept as printed and marked for review. Nothing here
assigns a feeding grade and nothing in the public site data is read for writing or changed.

Usage: python scripts/build_global_plant_evidence_research_v1.py --cache <dir> [--feedipedia-cache <dir>] [--offline]
"""
import argparse
import importlib.util
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "data/research"
COLUMNS = ["tortoise_key", "plant_as_printed", "plant_part", "offered_form", "wild_or_captive", "consumption_signal",
           "quantity_as_reported", "locality", "primary_reference_cited_by_source", "page", "evidence_type", "note"]
EVIDENCE_TYPES = {1: "direct_study_of_this_tortoise_species", 5: "specialist_husbandry_practice", 6: "local_knowledge_report"}
COMPOSITION_LABELS = {"dry matter", "crude protein", "crude fibre", "ndf", "adf", "lignin", "ether extract", "ash",
                      "calcium", "phosphorus", "potassium", "magnesium", "sodium", "starch", "total sugars",
                      "water-soluble carbohydrates", "oxalic acid", "nitrate", "tannins (eq. tannic acid)",
                      "tannins, condensed (eq. catechin)"}
GRADE_POLICY = "No feeding grade is assigned in the research layer. A record here is not a statement that the plant is safe to feed."


def has_printed_sample_count(nb):
    """A composition value is kept only when its own table row prints a sample count: an int from the shared parser.
    None is a blank Nb cell and '*' a calculated value without one; neither is kept (units 1, 2 and 5 use this rule)."""
    return isinstance(nb, int) and not isinstance(nb, bool)


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def dump(path, obj):
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")


def gbif(name, kingdom, cache, offline):
    key = re.sub(r"[^A-Za-z0-9]+", "_", "%s_%s" % (kingdom, name)).strip("_") + ".json"
    f = cache / key
    if f.exists():
        return load(f)
    if offline:
        return None
    url = "https://api.gbif.org/v1/species/match?" + urllib.parse.urlencode({"name": name, "kingdom": kingdom})
    d = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "tortoise-food-db-korea research"}), timeout=60))
    dump(f, d)
    time.sleep(0.4)
    return d


def name_rank(printed):
    """What rank the source itself names: species, genus, family, or a common name only."""
    s = printed.strip()
    if re.fullmatch(r"[A-Z][a-z]+(aceae|oideae)", s):
        return "family_or_subfamily"
    if "/" in s or "(" in s or not re.match(r"[A-Z][a-z]+", s) or re.search(r"\b(hay|leaves|pads|grass|grasses)\b", s):
        return "common_name_only"
    if re.fullmatch(r"[A-Z][a-z]+( (sp|spp)\.)?", s):
        return "genus"
    if re.fullmatch(r"[A-Z][a-z]+ [a-z-]+( (ssp|subsp|var)\. [a-z-]+)?", s):
        return "species"
    return "common_name_only"


def resolve(printed, cache, offline):
    rank = name_rank(printed)
    out = {"name_as_printed": printed, "rank_named_by_source": rank, "gbif_match_type": None, "gbif_status": None,
           "gbif_usage_key": None, "accepted_name": None, "accepted_key": None, "family": None, "name_check": "not_checked"}
    if rank == "common_name_only":
        out["name_check"] = "common_name_only_not_resolved"
        return out
    query = re.sub(r" (sp|spp)\.$", "", printed)
    d = gbif(query, "Plantae", cache, offline)
    if d is None:
        out["name_check"] = "not_checked_offline"
        return out
    out.update(gbif_match_type=d.get("matchType"), gbif_status=d.get("status"), gbif_usage_key=d.get("usageKey"), family=d.get("family"))
    want = {"species": ("SPECIES", "SUBSPECIES", "VARIETY", "FORM"), "genus": ("GENUS",), "family_or_subfamily": ("FAMILY", "SUBFAMILY")}[rank]
    same_name = (d.get("canonicalName") or "").lower() == query.lower()
    if rank == "species" and d.get("matchType") == "EXACT" and d.get("rank") in want:
        out["accepted_name"], out["accepted_key"] = d.get("species"), d.get("speciesKey")
        out["name_check"] = "accepted" if d.get("status") == "ACCEPTED" else "synonym_of_accepted_name" if d.get("status") == "SYNONYM" else "exact_match_status_" + str(d.get("status")).lower()
    elif rank == "genus" and same_name and d.get("rank") == "GENUS" and d.get("matchType") in ("EXACT", "HIGHERRANK"):
        # a genus name is kept as printed even when the backbone has sunk it into another genus: the source's scope must not widen
        out["accepted_name"], out["accepted_key"] = d.get("canonicalName"), d.get("usageKey")
        out["name_check"] = "accepted" if d.get("status") == "ACCEPTED" else "genus_kept_as_printed_backbone_status_" + str(d.get("status")).lower()
        if d.get("status") == "SYNONYM":
            out["backbone_genus"] = d.get("genus")
    elif rank == "family_or_subfamily" and same_name and d.get("rank") in want:
        out["accepted_name"], out["accepted_key"] = d.get("family") or d.get("canonicalName"), d.get("familyKey") or d.get("usageKey")
        out["name_check"] = "accepted" if d.get("status") == "ACCEPTED" else "synonym_of_accepted_name"
    elif d.get("matchType") == "FUZZY" and d.get("rank") in want:
        out["name_check"] = "spelling_differs_from_backbone_needs_review"
        out["gbif_fuzzy_candidate"] = d.get("canonicalName")
    else:
        out["name_check"] = "not_resolved_needs_review"
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True)
    ap.add_argument("--feedipedia-cache")
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--nutrition-only", action="store_true", help="rewrite only forage_nutrition_research_v1.json")
    a = ap.parse_args()
    cache = Path(a.cache)
    cache.mkdir(parents=True, exist_ok=True)
    tr = load(RES / "global_plant_evidence_transcription_v1.json")
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
            d = gbif("%s %s" % (m.group(1), m.group(2)), "Plantae", cache, a.offline)
            if d and d.get("matchType") == "EXACT" and d.get("species"):
                by_species.setdefault(d["species"], [])
                if p["id"] not in by_species[d["species"]]:
                    by_species[d["species"]].append(p["id"])

    # tortoise registry
    registry = []
    for key, t in tr["tortoises"].items():
        d = gbif(t["scientific_name"], "Animalia", cache, a.offline) or {}
        registry.append({"tortoise_key": key, "scientific_name": t["scientific_name"], "common_name_ko": t["common_name_ko"],
                         "common_name_en": t["common_name_en"], "names_in_sources": t["names_in_sources"],
                         "gbif_match_type": d.get("matchType"), "gbif_status": d.get("status"), "gbif_usage_key": d.get("usageKey"),
                         "gbif_accepted_name": d.get("species"), "family": d.get("family"),
                         "name_check": "accepted" if d.get("matchType") == "EXACT" and d.get("status") == "ACCEPTED" else
                         "synonym_in_gbif_backbone" if d.get("matchType") == "EXACT" and d.get("status") == "SYNONYM" else "needs_review"})

    resolved = {}

    def res(name):
        if name not in resolved:
            resolved[name] = resolve(name, cache, a.offline)
        return resolved[name]

    sources, evidence = [], []
    for sid, s in tr["sources"].items():
        status = {"full_text_read": "verified_primary_source" if s["source_type"] == "peer_reviewed_field_study" else "verified_in_peer_reviewed_account",
                  "abstract_only": "verified_abstract_only", "secondary_reproduction_only": "hold_original_not_read"}[s["access"]]
        sources.append({"source_id": sid, **{k: s[k] for k in ("citation", "url", "doi", "year", "language", "study_country", "publisher_country", "source_type", "method", "access", "what_was_read")},
                        "plant_record_count": len(s["records"]), "verification_status": status})
        for i, row in enumerate(s["records"], 1):
            r = dict(zip(COLUMNS, row))
            n = res(r["plant_as_printed"])
            primary_read = s["source_type"] == "peer_reviewed_field_study" and s["access"] == "full_text_read"
            evidence.append({
                "evidence_id": "%s-%02d" % (sid, i), "source_id": sid, "source_url": s["url"], "source_page": r["page"],
                "tortoise_key": r["tortoise_key"], "tortoise_scientific_name": tr["tortoises"][r["tortoise_key"]]["scientific_name"],
                "plant_name_as_printed": r["plant_as_printed"], "plant_accepted_name": n["accepted_name"], "plant_name_check": n["name_check"],
                "plant_rank_named_by_source": n["rank_named_by_source"], "plant_part": r["plant_part"], "preparation_state": r["offered_form"],
                "wild_or_captive": r["wild_or_captive"], "locality": r["locality"], "observed_consumption": r["consumption_signal"],
                "quantity_as_reported": r["quantity_as_reported"], "study_method": s["method"],
                "evidence_type": EVIDENCE_TYPES[r["evidence_type"]],
                "evidence_directness": "primary_study_read" if primary_read else "reported_in_account_primary_not_read" if r["primary_reference_cited_by_source"] else "statement_of_the_source_read",
                "primary_reference_cited_by_source": r["primary_reference_cited_by_source"],
                "is_negative_record": bool(re.search(r"avoid|reject", r["consumption_signal"])),
                "applies_to_other_tortoise_species": "not established by this source",
                "limitations": "Records what this tortoise taxon was reported to eat or be fed. It does not establish safe amounts, long-term outcomes or suitability for other tortoise species."
                               + (" " + r["note"][0].upper() + r["note"][1:] + "." if r["note"] else ""),
                "verification_status": status, "feeding_grade": None})

    for sid, c in tr["context_sources_without_plant_records"].items():
        sources.append({"source_id": sid, "citation": c["citation"], "url": c["url"], "doi": c.get("doi"), "year": c["year"], "language": c["language"],
                        "study_country": c["study_country"], "publisher_country": None, "source_type": "context_statement", "method": None,
                        "access": c["access"], "what_was_read": c["note"], "plant_record_count": 0, "tortoise_key": c["tortoise_key"],
                        "statement": c["statement"],
                        "verification_status": "verified_abstract_only" if c["access"] == "abstract_only" else "verified_in_peer_reviewed_account"})

    mixtures = []
    for m in tr["seed_mixtures"]:
        comps = []
        for sci, common, ratio in m["components"]:
            n = res(sci) if sci else {"accepted_name": None, "name_check": "common_name_only_not_resolved", "rank_named_by_source": "common_name_only"}
            comps.append({"scientific_name_as_printed": sci, "common_name_as_printed": common, "ratio_as_printed": ratio,
                          "accepted_name": n["accepted_name"], "name_check": n["name_check"]})
        mixtures.append({**{k: m[k] for k in ("mixture_id", "name", "supplier", "country", "language", "source_url", "source_type", "access",
                                              "target_tortoise_species", "ratios_basis", "cultivation_notes", "seed_treatment", "observed_consumption", "note")},
                         "existing_evidence_id": m.get("existing_evidence_id"), "component_count": len(comps), "components": comps,
                         "verification_status": "composition_transcribed_from_source",
                         "safety_statement": "A supplier or club listing a plant in a tortoise seed mix is not evidence that the plant is safe. Each component needs its own evidence."})

    # candidate plants: one row per accepted name (or per printed name when unresolved)
    cands = {}

    def touch(n, printed):
        key = n["accepted_name"] or "printed:" + printed
        c = cands.setdefault(key, {"candidate_key": key, "accepted_name": n["accepted_name"], "family": n.get("family"), "rank": n["rank_named_by_source"],
                                   "names_as_printed": [], "name_check": n["name_check"], "tortoise_taxa_with_records": [], "evidence_ids": [],
                                   "negative_record_only": None, "seed_mixture_ids": [], "existing_plant_ids": [], "existing_genus_level_plant_ids": [],
                                   "forage_nutrition_record_ids": [], "feeding_grade": None})
        if printed not in c["names_as_printed"]:
            c["names_as_printed"].append(printed)
        return c

    for e in evidence:
        c = touch(res(e["plant_name_as_printed"]), e["plant_name_as_printed"])
        c["evidence_ids"].append(e["evidence_id"])
        if e["tortoise_scientific_name"] not in c["tortoise_taxa_with_records"]:
            c["tortoise_taxa_with_records"].append(e["tortoise_scientific_name"])
    for m in mixtures:
        for comp in m["components"]:
            if comp["scientific_name_as_printed"]:
                c = touch(res(comp["scientific_name_as_printed"]), comp["scientific_name_as_printed"])
                if m["mixture_id"] not in c["seed_mixture_ids"]:
                    c["seed_mixture_ids"].append(m["mixture_id"])
    neg = {e["evidence_id"]: e["is_negative_record"] for e in evidence}
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

    # forage nutrition (Feedipedia tables selected for candidate plants)
    nutrition = []
    sel_path = RES / "forage_table_selection_v1.json"
    if sel_path.exists() and a.feedipedia_cache:
        spec = importlib.util.spec_from_file_location("v", ROOT / "scripts/verify_nutrition_reference_sources_v1.py")
        v = importlib.util.module_from_spec(spec)
        argv, sys.argv = sys.argv, ["x"]
        spec.loader.exec_module(v)
        sys.argv = argv
        for t in load(sel_path)["tables"]:
            page = Path(a.feedipedia_cache) / ("feedipedia_%s.html" % t["node"])
            if not page.exists():
                continue
            rows, title = v.parse_feedipedia(page.read_text(encoding="utf-8", errors="replace"))
            if not title or not rows:
                continue
            listed = t["table_name_in_datasheet"]
            page_note = None if title == listed or listed.endswith(title) else title
            title = listed
            low = title.lower()
            state =("hay" if "hay" in low else "fresh" if "fresh" in low else "dried" if re.search(r"dehydrated|dried|dry\b", low) else
                     "crop_residue" if re.search(r"straw|haulm|stover", low) else "not_stated")
            n = res(t["taxon"])
            values = [{"nutrient_name": lab, "nutrient_value": avg, "nutrient_unit": {"% as fed": "% as fed", "% dm": "% DM", "g/kg dm": "g/kg DM", "mg/kg dm": "mg/kg DM"}[unit],
                       "measurement_basis": "as fed" if unit == "% as fed" else "dry matter", "sample_count": nb}
                      for (lab, unit), (avg, nb) in rows.items() if lab in COMPOSITION_LABELS and has_printed_sample_count(nb) and unit in ("% as fed", "% dm", "g/kg dm", "mg/kg dm")]
            if not values:
                continue
            rid = "feedipedia-%s" % t["node"]
            nutrition.append({"record_id": rid, "source_name": "Feedipedia (INRAE, CIRAD, AFZ, FAO)", "source_id": str(t["node"]),
                              "source_url": "https://www.feedipedia.org/node/%s" % t["node"], "table_title_as_printed": title, "table_note_on_page": page_note, "datasheet": t["datasheet"],
                              "analyzed_taxon": t["taxon"], "analyzed_taxon_accepted_name": n["accepted_name"], "analyzed_part": title.split(",", 1)[1].strip() if "," in title else "not stated",
                              "preparation_state": state, "analytical_method": "compiled feed table; average of the samples counted in sample_count",
                              "values": values, "excluded_from_this_record": "values the source marks as calculated (*), and all ruminant, pig, poultry or rabbit energy and digestibility values",
                              "use_limits": "Livestock feed table. Not a tortoise digestibility or safety value. Fresh and hay tables come from different samples and must not be subtracted to estimate drying losses.",
                              "verification_status": "transcribed_by_parser_from_cached_source_page", "feeding_verdict_use": False})
            key = n["accepted_name"] or "printed:" + t["taxon"]
            if key in cands:
                cands[key]["forage_nutrition_record_ids"].append(rid)

    meta = {"schema_version": "1.0", "generated_by": "scripts/build_global_plant_evidence_research_v1.py", "generated_from": "data/research/global_plant_evidence_transcription_v1.json",
            "layer": "research_only_not_published", "grade_policy": GRADE_POLICY}
    if a.nutrition_only:
        dump(RES / "forage_nutrition_research_v1.json", {**meta, "records": nutrition})
        print("unit 1 (nutrition only): nutrition records %d, values %d" % (len(nutrition), sum(len(r["values"]) for r in nutrition)))
        return
    dump(RES / "global_evidence_sources_v1.json", {**meta, "sources": sources, "already_in_repository": tr["sources_already_in_repository"], "on_hold": tr["sources_on_hold"]})
    dump(RES / "tortoise_species_registry_v1.json", {**meta, "name_authority": "GBIF backbone taxonomy, species/match API", "species": registry})
    dump(RES / "tortoise_plant_evidence_v1.json", {**meta, "records": evidence})
    dump(RES / "enclosure_seed_mixtures_v1.json", {**meta, "mixtures": mixtures, "on_hold": tr["seed_mixtures_on_hold"]})
    dump(RES / "plant_candidates_v1.json", {**meta, "name_authority": "GBIF backbone taxonomy, species/match API",
                                            "candidates": sorted(cands.values(), key=lambda c: c["candidate_key"])})
    dump(RES / "forage_nutrition_research_v1.json", {**meta, "records": nutrition})
    print("sources %d, tortoise taxa %d, evidence %d, mixtures %d, candidates %d, nutrition records %d"
          % (len(sources), len(registry), len(evidence), len(mixtures), len(cands), len(nutrition)))


if __name__ == "__main__":
    main()
