#!/usr/bin/env python3
"""Exact-species fresh-mass flower records from open-access peer-reviewed studies.

Source of truth: data/academic_flower_nutrition_sources_20261009.json (tables parsed from the published
Europe PMC XML, with the XML SHA-256). Each adopted plant gets exactly one primary record built from one
study; a second study of the same species is kept as a separate crosscheck and is never averaged in.

  python scripts/build_academic_flower_nutrition_v1.py           # check: master records equal the source tables
  python scripts/build_academic_flower_nutrition_v1.py --apply   # write the records, move plants off the hold list,
                                                                   # log the screening in the research log

Conversion is mg/kg FM / 10 = mg/100 g FM (crude protein g/kg FM / 10 = g/100 g). Water is not derived from dry
matter (dry matter is kept as published in dry_matter_pct); fibre, vitamin C and energy were not measured.
"""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data/academic_flower_nutrition_sources_20261009.json"
NUT = ROOT / "data/plant_nutrition_v56.json"
HOLD = ROOT / "data/nutrition_hold_list_v1.json"
LOG = ROOT / "data/nutrition_global_research_log_v1.json"
PLANTS = ROOT / "data/plants.json"
VERIFIED_AT = "2026-10-09"
SOURCE_NAME = "Peer-reviewed journal article (open access)"
MINERALS = {"calcium": "calcium_mg", "phosphorus": "phosphorus_mg", "potassium": "potassium_mg",
            "magnesium": "magnesium_mg", "sodium": "sodium_mg", "iron": "iron_mg"}
TABLES = {"PMC6268292": "Tables 2–4", "PMC8472405": "Tables 4–6"}

load = lambda p: json.loads(p.read_text(encoding="utf-8"))
dump = lambda p, d: p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
div10 = lambda v: round(v / 10, 4)


def study_values(paper, row):
    vals = {MINERALS[k]: div10(v) for k, v in row["minerals_mg_per_kg_fresh_mass"].items()}
    vals["protein_g"] = div10(row["crude_protein_g_per_kg_fresh_mass"])
    vals["dry_matter_pct"] = row["dry_matter_pct_w_w"]
    vals["calcium_phosphorus_ratio"] = round(vals["calcium_mg"] / vals["phosphorus_mg"], 2)
    return vals


def build(src, plants):
    papers = {p["pmc"]: p for p in src["papers"]}
    find = lambda pmc, sp: next(r for r in papers[pmc]["rows"] if r["species_as_printed"] == sp)
    out = []
    for a in src["adopted"]:
        pid, paper = a["plant_id"], papers[a["pmc"]]
        row = find(a["pmc"], a["species_as_printed"])
        master = plants[pid]
        vals = study_values(paper, row)
        rec = {
            "plant_id": pid,
            "food_description": f"{row['species_as_printed']} '{row['cultivar']}' edible flowers, fresh (whole flowers at full bloom)",
            "source_name": SOURCE_NAME,
            "source_institution": paper["institution"],
            "source_country": "Czech Republic",
            "source_kind": "academic_peer_reviewed",
            "source_id": f"DOI {paper['doi']} {TABLES[a['pmc']]}",
            "source_doi": paper["doi"],
            "source_pmcid": paper["pmc"],
            "source_url": paper["source_url"],
            "source_license": paper["license"],
            "source_citation": paper["citation"],
            "fulltext_xml_sha256": paper["fulltext_xml_sha256"],
            "data_type": "Peer-reviewed study",
            "dataset_release": f"{paper['citation']} Full text XML via Europe PMC ({paper['pmc']}).",
            "source_scientific_name": row["species_as_printed"],
            "scientific_name": master["scientific"],
            "cultivar": row["cultivar"],
            "verification_status": "verified",
            "verified_at": VERIFIED_AT,
            "basis": "per 100 g fresh flower mass (published mg/kg FM divided by 10)",
            "plant_part": "flower",
            "preparation_state": "raw",
            "sample": paper["sample"],
            "sampling_location": paper["location"],
            "sampling_period": paper["period"],
            "n": 10,
            "identity_match_basis": f"{paper['pmc']} species/cultivar table: {row['species_as_printed']} '{row['cultivar']}' = master taxon {master['scientific']} (exact species)",
            "applicability_note_ko": f"체코 유리온실 재배 관상용 품종 '{row['cultivar']}'의 생화(꽃 전체) 분석값(2년 평균, n=10)이다. 잎·줄기에는 적용하지 않으며, 품종·재배 토양에 따라 무기질 함량이 달라질 수 있다.",
            "feeding_scope_note_ko": "성분 기술용 자료이며 급여 등급·빈도·안전성 판정에 사용하지 않는다.",
            "value_conventions": "Minerals published as mg/kg fresh mass and crude protein as g/kg FM (Kjeldahl N × 6.25) were divided by 10. Water was not measured as such and is not derived; dry matter (% w/w) is stored as published. Fibre, vitamin C and energy were not measured and are absent, not zero.",
            "units": {"protein_g": "g", "calcium_mg": "mg", "phosphorus_mg": "mg", "potassium_mg": "mg", "sodium_mg": "mg",
                      "magnesium_mg": "mg", "iron_mg": "mg", "dry_matter_pct": "% w/w"},
            **vals,
        }
        cc = a.get("crosscheck")
        if cc:
            cp, crow = papers[cc["pmc"]], find(cc["pmc"], cc["species_as_printed"])
            rec["independent_crosscheck"] = {"source_doi": cp["doi"], "source_pmcid": cp["pmc"], "source_url": cp["source_url"],
                                             "cultivar": crow["cultivar"], "sampling_period": cp["period"], "use": cc["use"],
                                             **study_values(cp, crow)}
        out.append(rec)
    return out


def main(apply):
    src, nut, plants = load(SRC), load(NUT), {p["id"]: p for p in load(PLANTS)}
    want = {r["plant_id"]: r for r in build(src, plants)}
    have = {r["plant_id"]: r for r in nut["plants"]}
    if not apply:
        errors = []
        for pid, r in want.items():
            if have.get(pid) != r:
                diff = sorted(k for k in set(r) | set(have.get(pid, {})) if r.get(k) != have.get(pid, {}).get(k))
                errors.append(f"{pid}: master record differs from source tables in {diff[:8]}")
        for pid, r in have.items():
            if r.get("source_kind") == "academic_peer_reviewed" and pid not in want:
                errors.append(f"{pid}: academic record without an adopted source entry")
        if errors:
            for e in errors: print("ERROR:", e)
            sys.exit(f"academic flower nutrition check FAILED: {len(errors)} error(s)")
        print(f"OK: {len(want)} academic flower records equal the published tables ÷ 10 ({', '.join(sorted(want))})")
        return

    nut["plants"] = [r for r in nut["plants"] if r["plant_id"] not in want] + list(want.values())
    dump(NUT, nut)

    hold = load(HOLD)
    hold["records"] = [h for h in hold["records"] if h["plant_id"] not in want]
    by_id = {h["plant_id"]: h for h in hold["records"]}
    for na in src["not_adopted"]:
        h = by_id.get(na["plant_id"])
        if h is None: continue
        ex = h.setdefault("international_candidates_examined", [])
        for rec in na["records"]:
            if not any(e.get("record") == rec for e in ex):
                ex.append({"source": "Europe PMC REST (fullTextXML)", "country": "Czech Republic", "record": rec, "decision": "held", "reason": na["reason"]})
    hold["held_count"] = len(hold["records"])
    summary = {}
    for h in hold["records"]: summary[h["hold_reason_code"]] = summary.get(h["hold_reason_code"], 0) + 1
    hold["summary"] = dict(sorted(summary.items()))
    dump(HOLD, hold)

    log = load(LOG)
    log["sources"] = [s for s in log["sources"] if s["id"] != "academic_open_access_flowers_2026"]
    log["sources"].append({
        "id": "academic_open_access_flowers_2026", "region": "Europe", "country": "Czech Republic",
        "institution": "Tomas Bata University in Zlín / Mendel University in Brno (peer-reviewed, MDPI open access)",
        "database": "Europe PMC open-access full text (peer-reviewed primary analyses)",
        "url": "https://www.ebi.ac.uk/europepmc/webservices/rest/", "access": "downloaded (public fullTextXML, CC BY)",
        "accessed_at": VERIFIED_AT, "method": "exact master binomial + flower part + fresh-mass unit; no cross-study averaging",
        "findings": [{"plant_id": a["plant_id"], "record": f"{a['pmc']} {a['species_as_printed']}", "decision": "adopted",
                      "reason": "exact species, whole fresh flower, mg/kg FM converted ÷10"} for a in src["adopted"]]
                    + [{"plant_id": na["plant_id"], "record": "; ".join(na["records"]), "decision": "held", "reason": na["reason"]}
                       for na in src["not_adopted"] if na["plant_id"] in by_id]
                    + [{"plant_id": "calendula", "record": f"{r['pmc']}", "decision": "rejected", "reason": r["reason"]}
                       for r in src["papers_screened_and_rejected"] if r["pmc"] == "PMC13295730"],
        "screened_and_rejected": src["papers_screened_and_rejected"]})
    dump(LOG, log)
    print(f"APPLIED: {len(want)} academic flower records; hold list now {hold['held_count']}")


if __name__ == "__main__":
    main("--apply" in sys.argv)
