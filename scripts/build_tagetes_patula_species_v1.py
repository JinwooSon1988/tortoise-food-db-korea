#!/usr/bin/env python3
"""만수국(Tagetes patula) species-level nutrition record, kept separate from the genus-level 메리골드 master.

Source of truth for the values: data/academic_flower_nutrition_sources_20261009.json (tables parsed from the
published Europe PMC XML, SHA-256 recorded). Each cultivar is its own record; the two studies are never averaged.

  python scripts/build_tagetes_patula_species_v1.py           # check (CI): species file equals the source tables / 10
  python scripts/build_tagetes_patula_species_v1.py --apply   # (re)write data/tagetes_patula_species_nutrition_v1.json

Structural limit (why this is not a separate public plant page yet): a public plant page requires a row in
data/public_assessments.json, a mapped verdict code in public_verdict.py/verdict-core.js and an evidence record
that names the plant. Those belong to the feeding-safety review and are deliberately not touched here, so
만수국 is published only as clearly scoped species cards on the 메리골드 (Tagetes spp.) page.
"""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data/academic_flower_nutrition_sources_20261009.json"
OUT = ROOT / "data/tagetes_patula_species_nutrition_v1.json"
MINERALS = {"calcium": "calcium_mg", "phosphorus": "phosphorus_mg", "potassium": "potassium_mg",
            "magnesium": "magnesium_mg", "sodium": "sodium_mg", "iron": "iron_mg"}
TABLES = {"PMC6268292": "Tables 1–4", "PMC8472405": "Tables 1, 4–6"}
MFDS = "https://www.foodsafetykorea.go.kr/portal/safefoodlife/foodMeterial/foodMeterialDB.do?menu_no=2968&menu_grp=MENU_NEW04"


def build():
    src = json.loads(SRC.read_text(encoding="utf-8"))
    records = []
    for paper in src["papers"]:
        for row in paper["rows"]:
            if row["species_as_printed"] != "Tagetes patula":
                continue
            vals = {MINERALS[k]: round(v / 10, 4) for k, v in row["minerals_mg_per_kg_fresh_mass"].items()}
            vals["protein_g"] = round(row["crude_protein_g_per_kg_fresh_mass"] / 10, 4)
            vals["dry_matter_pct"] = row["dry_matter_pct_w_w"]
            vals["calcium_phosphorus_ratio"] = round(vals["calcium_mg"] / vals["phosphorus_mg"], 2)
            records.append({
                "record_id": f"tagetes_patula_{row['cultivar'].lower().replace(' ', '_')}",
                "cultivar": row["cultivar"],
                "source_scientific_name": row["species_as_printed"],
                "plant_part": "flower (whole fresh flowers at full bloom)",
                "preparation_state": "raw (fresh)",
                "basis": "per 100 g fresh flower mass (published mg/kg FM divided by 10)",
                "n": 10,
                "sampling_location": paper["location"],
                "sampling_period": paper["period"],
                "source_citation": paper["citation"],
                "source_doi": paper["doi"],
                "source_url": paper["source_url"],
                "source_pmcid": paper["pmc"],
                "source_tables": TABLES[paper["pmc"]],
                "source_license": paper["license"],
                "fulltext_xml_sha256": paper["fulltext_xml_sha256"],
                "verification_status": "verified",
                "verified_at": "2026-10-09",
                **vals,
                "not_measured": ["water_g", "fiber_g", "vitamin_c_mg", "vitamin_a_rae_ug", "energy_kcal"],
            })
    return {
        "schema_version": "1.0",
        "species_id": "tagetes_patula",
        "ko": "만수국",
        "en": "French marigold",
        "scientific_name": "Tagetes patula L.",
        "parent_master_plant_id": "marigold",
        "parent_master_scientific": "Tagetes spp.",
        "identity": {
            "korean_name_source": {"name": "MFDS 식품원료목록", "record": "#628 만수국 — French marigold — Tagetes patula L. (사용부위 꽃)", "url": MFDS, "checked_at": "2026-10-09"},
            "global_backbone": {"name": "GBIF Backbone Taxonomy", "record": "Tagetes patula L. (usageKey 3088492) = SYNONYM of Tagetes erecta L. (3088488)", "url": "https://www.gbif.org/species/3088492", "checked_at": "2026-10-09"},
            "taxonomic_note": "식약처는 만수국을 Tagetes patula L.로 등록한다. GBIF 백본(WCVP 계열)은 T. patula를 T. erecta의 이명으로 처리하므로, 분류 체계에 따라 아프리칸메리골드와 한 종으로 묶일 수 있다. 원논문은 두 편 모두 'Tagetes patula'로 표기했다.",
            "not_checked": "POWO (Cloudflare challenge; not bypassed)",
        },
        "publication": {
            "public_plant_page": False,
            "shown_on": "plant/marigold/index.html (nutrition section, species cards)",
            "structural_reason": "A separate public page needs a public_assessments.json row, a verdict code mapped in public_verdict.py and verdict-core.js, and an evidence record naming the plant; these belong to the feeding-safety review and were not modified.",
        },
        "feeding_verdict": {
            "status": "not_assessed",
            "display_ko": "만수국만을 대상으로 한 급여 판정은 없다(판정 보류).",
            "inheritance": "The genus-level 메리골드 verdict is not inherited automatically.",
            "context_ko": "전문 육지거북 DB(The Tortoise Table)는 French Marigold를 포함한 Tagetes spp. 전체를 ‘급여하지 않음’으로 분류한다. 판정 보류는 급여해도 된다는 뜻이 아니다.",
            "context_source": "https://www.thetortoisetable.org.uk/plant-database/viewplants/?plant=314&c=5",
        },
        "policy": {"no_averaging_across_studies": True, "no_other_species_or_part_values": True, "nutrition_is_not_safety_evidence": True},
        "records": records,
    }


def main(apply):
    want = build()
    if apply:
        OUT.write_text(json.dumps(want, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"APPLIED: {len(want['records'])} Tagetes patula cultivar records")
        return
    have = json.loads(OUT.read_text(encoding="utf-8"))
    errors = []
    if have != want:
        errors.append("data/tagetes_patula_species_nutrition_v1.json differs from the published source tables / 10")
    plants = {p["id"]: p for p in json.loads((ROOT / "data/plants.json").read_text(encoding="utf-8"))}
    if plants.get("marigold", {}).get("scientific") != "Tagetes spp.":
        errors.append("genus-level 메리골드 master must stay Tagetes spp. (no bulk rename to T. patula)")
    nut = {r["plant_id"] for r in json.loads((ROOT / "data/plant_nutrition_v56.json").read_text(encoding="utf-8"))["plants"]}
    if "marigold" in nut:
        errors.append("species values must not be promoted into the genus-level marigold master nutrition")
    if len({r["cultivar"] for r in have["records"]}) != len(have["records"]) or len(have["records"]) != 2:
        errors.append("expected exactly two separate cultivar records")
    page = (ROOT / "plant/marigold/index.html").read_text(encoding="utf-8")
    i = page.index('<section class="card" id="nutrition">'); sec = page[i:page.index("</section>", i)]
    if "검증된 영양자료 없음" not in sec:
        errors.append("marigold master nutrition must stay '검증된 영양자료 없음'")
    for r in have["records"]:
        for needle in (r["cultivar"], r["source_url"], f"<strong>{r['calcium_mg']}mg</strong>", f"<strong>{r['phosphorus_mg']}mg</strong>",
                       f"<strong>{r['calcium_phosphorus_ratio']}:1</strong>", f"<strong>{r['dry_matter_pct']}%</strong>"):
            if needle not in sec: errors.append(f"marigold page: card for {r['cultivar']} missing {needle!r}")
    for needle in ("판정 보류", "급여하지 않음", "메리골드 전체", "미확인", "../../data/tagetes_patula_species_nutrition_v1.json"):
        if needle not in sec: errors.append(f"marigold page: missing {needle!r}")
    if errors:
        for e in errors: print("ERROR:", e)
        sys.exit(f"Tagetes patula species QA FAILED: {len(errors)} error(s)")
    print("OK: 2 Tagetes patula cultivar records equal the published tables / 10; genus master unchanged; cards scoped on the marigold page")


if __name__ == "__main__":
    main("--apply" in sys.argv)
