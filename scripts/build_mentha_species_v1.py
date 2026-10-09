#!/usr/bin/env python3
"""페퍼민트(Mentha × piperita)·스피어민트(Mentha spicata) species-level nutrition, kept apart from the
genus-level 민트(Mentha spp.) master and its feeding verdict.

  python scripts/build_mentha_species_v1.py --csv FoodData_Central_sr_legacy_food_csv_2018-04.zip --apply
      rebuild data/mentha_species_nutrition_v1.json from the ORIGINAL USDA SR Legacy CSV archive
  python scripts/build_mentha_species_v1.py --csv FoodData_Central_sr_legacy_food_csv_2018-04.zip
      verify the stored values against the archive (exit 1 on any difference)
  python scripts/build_mentha_species_v1.py
      CI check without the archive: internal consistency, agreement with the independently audited
      data/usda_mint_variety_candidates_20261009.json, genus master untouched, page cards rendered from data

Only analytical (derivation A) values are stored; calculated values (carbohydrate, energy: NC) are listed as
not shown. Dried mint is never converted. The RDA 페퍼민트_생것 record is a literature-collected copy of USDA
data and is recorded as not independent.
"""
import csv, hashlib, io, json, sys, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/mentha_species_nutrition_v1.json"
NBR = {"255": "water_g", "203": "protein_g", "291": "fiber_g", "301": "calcium_mg", "305": "phosphorus_mg", "306": "potassium_mg",
       "307": "sodium_mg", "304": "magnesium_mg", "303": "iron_mg", "401": "vitamin_c_mg", "320": "vitamin_a_rae_ug",
       "204": "fat_g", "205": "carbohydrate_g", "208": "energy_kcal"}
MFDS = "https://www.foodsafetykorea.go.kr/portal/safefoodlife/foodMeterial/foodMeterialDB.do?menu_no=2968&menu_grp=MENU_NEW04"
SPECIES = {
    "peppermint": {
        "ko": "페퍼민트", "en": "Peppermint", "scientific_name": "Mentha × piperita L.", "fdc_id": 173474,
        "usda_scientific_name": "Mentha x piperita L. nothosubsp. piperita",
        "synonyms_or_names": ["서양박하 (식약처 원료명)", "Mentha piperita (The Tortoise Table 표기)"],
        "mfds": "#1009 서양박하 — 이명 페퍼민트, Peppermint — Mentha x piperita L. (사용부위 잎)",
        "gbif": {"key": 8707933, "name": "Mentha × piperita L.", "status": "ACCEPTED"},
        "not_same_as": "식약처 #774 ‘박하’(Mentha arvensis var. piperascens; GBIF에서 Mentha canadensis L.의 이명)는 영문 별칭이 Peppermint이지만 다른 종이다.",
        "feeding_context": {"source": "The Tortoise Table", "entry": "Peppermint (Mentha piperita)", "classification": "Do not Feed",
                            "classification_ko": "급여하지 않음", "reason_quote": "Peppermint contains the natural organic compound pulegone (also found in Pennyroyal), which has been found to cause liver damage and to be toxic to rats if consumed in large quantities.",
                            "reason_ko": "페니로열과 같은 풀레곤 성분을 근거로 급여 제외를 권한다(쥐 대량 섭취 독성 근거).",
                            "url": "https://www.thetortoisetable.org.uk/plant-database/viewplants/?plant=512", "checked_at": "2026-10-09"},
    },
    "spearmint": {
        "ko": "스피어민트", "en": "Spearmint", "scientific_name": "Mentha spicata L.", "fdc_id": 173475,
        "usda_scientific_name": "Mentha spicata",
        "synonyms_or_names": ["녹양박하 (식약처 원료명)", "Mentha viridis (L.) L. (이명)"],
        "mfds": "#387 녹양박하 — 이명 스피어민트, 양박하, Spearmint — Mentha spicata L. / Mentha viridis L. (사용부위 잎)",
        "gbif": {"key": 2927175, "name": "Mentha spicata L.", "status": "ACCEPTED", "synonym_checked": "Mentha viridis (L.) L. = SYNONYM (accepted Mentha spicata subsp. spicata)"},
        "not_same_as": "페퍼민트(Mentha × piperita)·페니로열(Mentha pulegium)과 다른 종이다.",
        "feeding_context": {"source": "The Tortoise Table", "entry": "Mint (Garden Mint, Spearmint, Apple Mint) — Mentha sachalinensis; M. spicata, M. suaveolens", "classification": "Safe to Feed",
                            "classification_ko": "급여 가능", "reason_quote": "do not confuse these mints with Peppermint (Mentha piperita), Pennyroyal (Mentha pulegium) or Purple Mint (Perilla)",
                            "reason_ko": "가든민트·애플민트와 함께 묶인 항목으로 분류하며, 페퍼민트·페니로열과 혼동하지 말라고 경고한다. 급여 비율·빈도나 거북 대상 시험 근거는 제시하지 않는다.",
                            "url": "https://www.thetortoisetable.org.uk/plant-database/viewplants/?plant=506", "checked_at": "2026-10-09"},
    },
}


def from_csv(zip_path):
    z = zipfile.ZipFile(zip_path)
    rows = lambda n: csv.DictReader(io.TextIOWrapper(z.open(next(m for m in z.namelist() if m.endswith("/" + n))), encoding="utf-8-sig"))
    nut = {r["id"]: NBR[r["nutrient_nbr"]] for r in rows("nutrient.csv") if r["nutrient_nbr"] in NBR and not (r["nutrient_nbr"] == "208" and r["unit_name"].upper() != "KCAL")}
    der = {r["id"]: r["code"] for r in rows("food_nutrient_derivation.csv")}
    ids = {str(s["fdc_id"]) for s in SPECIES.values()}
    desc = {r["fdc_id"]: r["description"] for r in rows("food.csv") if r["fdc_id"] in ids}
    vals = {}
    for r in rows("food_nutrient.csv"):
        if r["fdc_id"] in ids and r["nutrient_id"] in nut:
            vals.setdefault(r["fdc_id"], {})[nut[r["nutrient_id"]]] = (float(r["amount"]), int(r["data_points"] or 0), der.get(r["derivation_id"], "?"))
    sha = hashlib.sha256(Path(zip_path).read_bytes()).hexdigest()
    return desc, vals, sha


def build(zip_path):
    desc, vals, sha = from_csv(zip_path)
    species = []
    for key, s in SPECIES.items():
        fid = str(s["fdc_id"]); v = vals[fid]
        analytical = {k: (int(a) if a.is_integer() else a) for k, (a, n, d) in v.items() if d == "A"}
        species.append({
            "species_key": key, "ko": s["ko"], "en": s["en"], "scientific_name": s["scientific_name"],
            "synonyms_or_names": s["synonyms_or_names"], "not_same_as": s["not_same_as"],
            "identity_sources": [
                {"name": "MFDS 식품원료목록", "record": s["mfds"], "url": MFDS, "checked_at": "2026-10-09"},
                {"name": "GBIF Backbone Taxonomy", "record": s["gbif"], "url": f"https://www.gbif.org/species/{s['gbif']['key']}", "checked_at": "2026-10-09"},
                {"name": "USDA FoodData Central SR Legacy scientificName", "record": s["usda_scientific_name"], "checked_at": "2026-10-09"}],
            "nutrition": {
                "source_name": "USDA FoodData Central", "data_type": "SR Legacy", "release": "2018-04",
                "fdc_id": s["fdc_id"], "food_description": desc[fid],
                "source_url": f"https://fdc.nal.usda.gov/food-details/{s['fdc_id']}/nutrients",
                "archive": "FoodData_Central_sr_legacy_food_csv_2018-04.zip", "archive_sha256": sha,
                "basis": "per 100 g fresh (raw) edible portion",
                "plant_part": "not stated by USDA (household portions are expressed in leaves)",
                "preparation_state": "raw (fresh)",
                "values": analytical,
                "data_points": {k: n for k, (a, n, d) in v.items() if d == "A"},
                "derivation": "A (analytical) for every stored value",
                "not_shown_calculated": sorted(k for k, (a, n, d) in v.items() if d != "A"),
                "calcium_phosphorus_ratio": round(analytical["calcium_mg"] / analytical["phosphorus_mg"], 2),
                "unconfirmed": ["analysed plant part (USDA does not state it)"],
                "dried_records_not_converted": "USDA FDC 172239 Spearmint, dried and RDA 민트_말린것 are dried products and are never converted to fresh values.",
            },
            "feeding": {
                "site_verdict_status": "review_pending",
                "site_verdict_display_ko": "검토 보류 — 이 종에 대한 사이트 급여 등급은 아직 없다.",
                "inheritance": "The genus-level 민트(Mentha spp.) verdict is not inherited.",
                "specialist_database_context": s["feeding_context"],
                "nutrition_is_not_safety": True,
            },
            "image": {"status": "not_verified", "display_ko": "종별 검증 사진 없음"},
        })
    return {
        "schema_version": "1.0", "created_at": "2026-10-09",
        "parent_master_plant_id": "mint", "parent_master_scientific": "Mentha spp.",
        "purpose": "Separate species-level nutrition for peppermint and spearmint without changing the genus-level mint master or its verdict.",
        "publication": {"public_plant_pages": False, "shown_on": "plant/mint/index.html (species sections)",
                        "structural_reason": "Separate public plant pages require rows in data/public_assessments.json, a verdict code in public_verdict.py/verdict-core.js and evidence records naming the plants; those files belong to the separate feeding-safety review and were not modified."},
        "replaces_display_of": "data/usda_mint_variety_candidates_20261009.json (same FDC records; the candidate file is kept as history and no longer rendered, so each FDC record is shown once)",
        "rda_peppermint_record": {"source_id": "R118-059000001-0000", "food_description": "페퍼민트_생것", "data_generation_method": "수집 (literature-collected, 2018-12-31)",
                                  "independence": "not independent: water, protein, fat, carbohydrate, fibre, Ca, P, K, Na, Fe and vitamin C equal USDA FDC 173474; vitamin A differs (RDA 0 vs USDA 212 µg RAE) and RDA states refuse 39%",
                                  "decision": "not used"},
        "species": species,
    }


def check_ci():
    errors = []
    d = json.loads(OUT.read_text(encoding="utf-8"))
    cand = {r["fdc_id"]: r for r in json.loads((ROOT / "data/usda_mint_variety_candidates_20261009.json").read_text(encoding="utf-8"))["records"]}
    plants = {p["id"]: p for p in json.loads((ROOT / "data/plants.json").read_text(encoding="utf-8"))}
    if plants["mint"]["scientific"] != "Mentha spp.": errors.append("mint master must stay Mentha spp.")
    if any(r["plant_id"] == "mint" for r in json.loads((ROOT / "data/plant_nutrition_v56.json").read_text(encoding="utf-8"))["plants"]):
        errors.append("species values must not be promoted into the genus-level mint master nutrition")
    if {s["species_key"] for s in d["species"]} != {"peppermint", "spearmint"}: errors.append("expected peppermint and spearmint")
    page = (ROOT / "plant/mint/index.html").read_text(encoding="utf-8")
    i = page.index('<section class="card" id="nutrition">'); sec = page[i:page.index("</section>", i)]
    if "검증된 영양자료 없음" not in sec: errors.append("mint master nutrition must stay '검증된 영양자료 없음'")
    if sec.count('class="varietycard"') != 2: errors.append("each FDC record must be shown exactly once (2 cards)")
    for s in d["species"]:
        n = s["nutrition"]; v = n["values"]; c = cand[n["fdc_id"]]
        for k in ("water_g", "protein_g", "fiber_g", "calcium_mg", "phosphorus_mg", "potassium_mg", "vitamin_c_mg"):
            if v.get(k) != c.get(k): errors.append(f"{s['species_key']}: {k} {v.get(k)} != independently audited {c.get(k)}")
        if abs(n["calcium_phosphorus_ratio"] - v["calcium_mg"] / v["phosphorus_mg"]) > 0.006: errors.append(f"{s['species_key']}: Ca:P mismatch")
        if s["feeding"]["site_verdict_status"] != "review_pending": errors.append(f"{s['species_key']}: no site grade may be assigned here")
        if sec.count(f"FDC {n['fdc_id']}") != 1: errors.append(f"{s['species_key']}: FDC {n['fdc_id']} must appear in exactly one card")
        for needle in (s["ko"], n["source_url"], f"<strong>{v['calcium_mg']}mg</strong>", f"<strong>{v['phosphorus_mg']}mg</strong>",
                       f"<strong>{n['calcium_phosphorus_ratio']}:1</strong>", f"<strong>{v['fiber_g']}g</strong>", f"<strong>{v['water_g']}g</strong>",
                       s["feeding"]["specialist_database_context"]["url"], s["feeding"]["specialist_database_context"]["classification_ko"], "검토 보류", "종별 검증 사진 없음"):
            if needle not in sec: errors.append(f"mint page: {s['species_key']} missing {needle!r}")
    if "usda_mint_variety_candidates_20261009.json" in sec: errors.append("old candidate cards must not be rendered next to the species sections")
    if errors:
        for e in errors: print("ERROR:", e)
        sys.exit(f"Mentha species QA FAILED: {len(errors)} error(s)")
    print("OK: peppermint and spearmint species records consistent with audited USDA values; genus master and verdict untouched; each FDC shown once")


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--csv" in args:
        zip_path = args[args.index("--csv") + 1]
        want = build(zip_path)
        if "--apply" in args:
            OUT.write_text(json.dumps(want, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"); print("APPLIED from original USDA CSV")
        else:
            have = json.loads(OUT.read_text(encoding="utf-8"))
            if have != want: sys.exit("stored species file differs from the original USDA CSV")
            print("OK: species file equals the original USDA SR Legacy CSV")
    else:
        check_ci()
