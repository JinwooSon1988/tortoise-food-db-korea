#!/usr/bin/env python3
"""Add source-checked REFERENCE nutrition records (2026-10-10 batch) to data/plant_nutrition_reference_v1.json.

Every number is read from the original source file at build time; nothing is typed in by hand. Sources (download them
into --cache first):
  * Feedipedia table pages      https://www.feedipedia.org/node/<N>        -> feedipedia_<N>.html (crawl-delay 10 s)
  * MEXT Japan (2023)            https://fooddb.mext.go.jp/details/details.pl?ITEM_NO=6_<code>_7 -> mext_<code>.html
  * USDA FoodData Central SR Legacy JSON 2018-04 (FoodData_Central_sr_legacy_food_json_2018-04.json, --usda)
  * RDA 농촌진흥청 통합식품영양성분정보(원재료성식품) CSV 2025-12-23 (data.go.kr 15100065, --rda)
  * Indian Food Composition Tables 2017 PDF (nin.res.in/ebooks/IFCT2017.pdf, --ifct) for C030 minerals
  * PMC open-access XML (NCBI E-utilities efetch db=pmc) for PMC8472405 (--pmc-8472405)

Rules (docs/NUTRITION_REFERENCE_SOURCE_VERIFICATION_20261010.md): a record is REFERENCE when the source is the same
plant part of a related taxon, or a related part (stems+leaves, aerial forage, sprouts) of the same taxon, or a
dry-matter forage table. Fruit, seed or grain values are never linked to a leaf/flower plant. Units and basis are kept
exactly as published; dry-matter values are never converted to fresh weight. Nothing here is a feeding verdict.

  python scripts/build_nutrition_reference_batch_20261010.py --cache DIR --usda SR.json --rda RDA.csv --ifct IFCT.pdf \
      --pmc-8472405 pmc_8472405.xml [--dry-run]
"""
import argparse, csv, io, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import verify_nutrition_reference_sources_v1 as V  # noqa: E402

TODAY = "2026-10-10"
DM_UNITS = {"dry_matter_pct_as_fed": "% as fed"}
for k, (lab, unit) in V.FEEDIPEDIA_LABELS.items():
    DM_UNITS[k] = {"% dm": "% DM", "g/kg dm": "g/kg DM", "mg/kg dm": "mg/kg DM", "mj/kg dm": "MJ/kg DM", "% as fed": "% as fed"}[unit]
FRESH_UNITS = {"water_g": "g/100g", "protein_g": "g/100g", "fat_g": "g/100g", "carbohydrate_g": "g/100g", "fiber_g": "g/100g",
               "ash_g": "g/100g", "calcium_mg": "mg/100g", "phosphorus_mg": "mg/100g", "magnesium_mg": "mg/100g",
               "potassium_mg": "mg/100g", "sodium_mg": "mg/100g", "iron_mg": "mg/100g", "zinc_mg": "mg/100g",
               "vitamin_c_mg": "mg/100g"}
COMMON = {"status": "reference_only", "primary_eligible": False, "feeding_verdict_use": False}
DM_NOTE_KO = "Feedipedia 사료 성분표 값입니다. 건물 함량을 제외한 영양성분은 건조물 기준이며 생체 100g 기준으로 환산하지 않았습니다. 항목별 표본 수(n)가 달라 한 시료의 완전한 조성으로 해석하지 마세요. 급여 안전성 판정과는 별개입니다."
DM_NOTE_EN = "Feedipedia feed-table values. Apart from dry matter, nutrients are on a dry-matter basis and have not been converted to fresh weight. Sample counts (n) differ by nutrient, so do not read them as one sample's full composition. Separate from the feeding-safety assessment."
FRESH_NOTE_KO = "생체 가식부 100g 기준 원자료 값입니다. 급여 안전성 판정과는 별개입니다."
FRESH_NOTE_EN = "Values per 100 g raw edible portion as published. Separate from the feeding-safety assessment."

# ---------------------------------------------------------------- new records
FEEDIPEDIA = [
    # node, plant_id, tier, scientific name in source, analyzed part, scope ko, scope en, extra caution ko, extra caution en
    (11954, "celeryleaf", "dry_matter_reference", "Apium graveolens", "leaves", "셀러리 잎, 생초 시료의 건조물 기준(표본 1~2개)",
     "Celery leaves, fresh sample, dry-matter basis (n = 1–2)", "표본이 1~2개뿐입니다.", "Only 1–2 samples."),
    (12132, "grapevineleaf", "dry_matter_reference", "Vitis vinifera", "leaves", "포도(Vitis vinifera) 잎, 생초 시료의 건조물 기준. 머루(Vitis amurensis)와 다른 종",
     "Grape (Vitis vinifera) leaves, fresh sample, dry-matter basis; a different species from Amur grape (Vitis amurensis)",
     "머루가 아닌 포도 잎 자료입니다.", "These are grapevine, not Amur grape, leaves."),
    (25609, "buckwheatleaf", "dry_matter_reference", "Fagopyrum esculentum", "aerial part (leaves and stems)", "메밀 지상부(잎·줄기) 생초의 건조물 기준",
     "Buckwheat aerial part (leaves and stems), fresh, dry-matter basis", "잎만의 수치가 아닙니다.", "Not leaf-only."),
    (12667, "sunflowerleaf", "dry_matter_reference", "Helianthus annuus", "forage (aerial part)", "해바라기 사료용 생초(지상부)의 건조물 기준",
     "Sunflower fresh forage (aerial part), dry-matter basis", "잎만의 수치가 아니며 생육 단계가 다를 수 있습니다.", "Not leaf-only; growth stage may differ."),
    (22237, "cornleaf", "dry_matter_reference", "Zea mays", "leaves", "옥수수 잎, 생초 시료의 건조물 기준",
     "Maize leaves, fresh sample, dry-matter basis", "", ""),
    (12540, "comfrey", "dry_matter_reference", "Symphytum × uplandicum", "aerial part", "러시안 컴프리(Symphytum × uplandicum) 지상부 생초의 건조물 기준. 컴프리(S. officinale)와 다른 교잡종",
     "Russian comfrey (Symphytum × uplandicum) aerial part, fresh, dry-matter basis; a hybrid distinct from common comfrey (S. officinale)",
     "컴프리(S. officinale) 자체의 자료가 아닙니다.", "Not data for common comfrey (S. officinale) itself."),
    (12324, "melonleaf", "dry_matter_reference", "Cucumis melo", "aerial part", "멜론 지상부(잎·줄기) 생초의 건조물 기준(표본 1개)",
     "Melon aerial part (leaves and stems), fresh, dry-matter basis (n = 1)", "표본이 1개뿐이며 잎만의 수치가 아닙니다.", "Only 1 sample; not leaf-only."),
    (12741, "watermelonleaf", "dry_matter_reference", "Citrullus lanatus", "aerial part", "수박 지상부(잎·줄기) 생초의 건조물 기준(표본 1개)",
     "Watermelon aerial part (leaves and stems), fresh, dry-matter basis (n = 1)", "표본이 1개뿐이며 잎만의 수치가 아닙니다.", "Only 1 sample; not leaf-only."),
    (12761, "wheatleaf", "dry_matter_reference", "Triticum aestivum", "forage (whole aerial part)", "밀 사료용 생초(지상부 전체)의 건조물 기준",
     "Wheat fresh forage (whole aerial part), dry-matter basis", "잎만의 수치가 아니며 사료 수확 단계 자료입니다.", "Not leaf-only; forage harvest stage."),
    (12761, "wheatgrass", "dry_matter_reference", "Triticum aestivum", "forage (whole aerial part)", "밀 사료용 생초(지상부 전체)의 건조물 기준. 어린 밀싹과 생육 단계가 다름",
     "Wheat fresh forage (whole aerial part), dry-matter basis; a later growth stage than young wheatgrass",
     "어린 밀싹이 아니라 사료 수확 단계의 밀 지상부입니다.", "This is wheat at forage stage, not young wheatgrass."),
    (11831, "barleyleaf", "dry_matter_reference", "Hordeum vulgare", "aerial part", "보리 지상부 생초의 건조물 기준",
     "Barley aerial part, fresh, dry-matter basis", "잎만의 수치가 아니며 사료 수확 단계 자료입니다.", "Not leaf-only; forage harvest stage."),
    (11831, "barleygrass", "dry_matter_reference", "Hordeum vulgare", "aerial part", "보리 지상부 생초의 건조물 기준. 어린 보리싹과 생육 단계가 다름",
     "Barley aerial part, fresh, dry-matter basis; a later growth stage than young barley grass",
     "어린 보리싹이 아니라 사료 수확 단계의 보리 지상부입니다.", "This is barley at forage stage, not young barley grass."),
    (12390, "oatleaf", "dry_matter_reference", "Avena sativa", "forage (whole aerial part)", "귀리 사료용 생초(지상부 전체)의 건조물 기준",
     "Oat fresh forage (whole aerial part), dry-matter basis", "잎만의 수치가 아니며 사료 수확 단계 자료입니다.", "Not leaf-only; forage harvest stage."),
    (12390, "oatgrass", "dry_matter_reference", "Avena sativa", "forage (whole aerial part)", "귀리 사료용 생초(지상부 전체)의 건조물 기준. 어린 귀리싹과 생육 단계가 다름",
     "Oat fresh forage (whole aerial part), dry-matter basis; a later growth stage than young oat grass",
     "어린 귀리싹이 아니라 사료 수확 단계의 귀리 지상부입니다.", "This is oat at forage stage, not young oat grass."),
    (11595, "pricklypear", "dry_matter_reference", "Opuntia ficus-indica", "cladode (pad)", "손바닥선인장(Opuntia ficus-indica) 줄기(패드) 생시료의 건조물 기준. 천년초와 같은 종인지 확인되지 않음",
     "Prickly pear (Opuntia ficus-indica) cladodes, fresh, dry-matter basis; not confirmed to be the same species as Korean cheonnyeoncho",
     "천년초(Opuntia spp.)와 종이 다를 수 있습니다.", "The species may differ from the Korean Opuntia sold as cheonnyeoncho."),
    (12762, "clover", "dry_matter_reference", "Trifolium repens", "aerial part", "화이트클로버(Trifolium repens) 지상부 생초의 건조물 기준. 클로버류(속) 전체의 대표값 아님",
     "White clover (Trifolium repens) aerial part, fresh, dry-matter basis; not representative of all clovers",
     "클로버 한 종(T. repens)의 자료입니다.", "Data for one clover species (T. repens)."),
    (12508, "clover", "dry_matter_reference", "Trifolium pratense", "aerial part", "레드클로버(Trifolium pratense) 지상부 생초의 건조물 기준. 클로버류(속) 전체의 대표값 아님",
     "Red clover (Trifolium pratense) aerial part, fresh, dry-matter basis; not representative of all clovers",
     "클로버 한 종(T. pratense)의 자료입니다.", "Data for one clover species (T. pratense)."),
    (12012, "vicia_cracca", "dry_matter_reference", "Vicia sativa", "aerial part", "살갈퀴(Vicia sativa) 지상부 생초의 건조물 기준. 등갈퀴나물(Vicia cracca)과 다른 종",
     "Common vetch (Vicia sativa) aerial part, fresh, dry-matter basis; a different species from tufted vetch (Vicia cracca)",
     "등갈퀴나물이 아닌 같은 속 다른 종의 자료입니다.", "Data for a different species of the same genus."),
]
MEXT = [
    ("06075", "celeryleaf", "related_part_reference", "stems and leaves", "잎셀러리(キンサイ, Apium graveolens var. secalinum) 생줄기·생잎 혼합 분석",
     "Leaf celery (Apium graveolens var. secalinum), raw stems and leaves analysed together",
     "잎만의 수치가 아니며 잎셀러리 변종 자료입니다.", "Not leaf-only; data for the leaf-celery variety."),
]
USDA = [
    (170076, "dock", "related_species_reference", "leaves (raw greens)", "소리쟁이류(Rumex spp.) 생잎, 종 미특정",
     "Dock (Rumex spp.), raw greens; species not specified", "종이 특정되지 않은 소리쟁이속 자료입니다.", "Genus-level data; the species is not specified."),
    (169270, "pumpkinflower", "related_species_reference", "flowers", "호박류(Cucurbita spp.) 생꽃, 종 미특정",
     "Pumpkin (Cucurbita spp.) flowers, raw; species not specified", "종이 특정되지 않은 호박속 자료입니다.", "Genus-level data; the species is not specified."),
    (168575, "grapevineleaf", "related_species_reference", "leaves", "포도(Vitis vinifera) 생잎. 머루(Vitis amurensis)와 다른 종",
     "Grape (Vitis vinifera) leaves, raw; a different species from Amur grape (Vitis amurensis)",
     "머루가 아닌 포도 잎 자료입니다.", "These are grapevine, not Amur grape, leaves."),
    (170481, "borage", "related_part_reference", "part not stated by source", "보리지(Borago officinalis) 생것. USDA 원자료가 잎·꽃 등 부위를 밝히지 않음",
     "Borage (Borago officinalis), raw; USDA does not state the plant part", "분석 부위가 표기되지 않았습니다.", "The analysed part is not stated."),
    (168571, "pricklypear", "related_species_reference", "cladode (pad)", "노팔(Nopalea cochenillifera, 일부 분류에서 Opuntia cochenillifera) 생줄기(패드)",
     "Nopales (Nopalea cochenillifera, treated as Opuntia cochenillifera in some classifications), raw pads",
     "천년초와 다른 종의 자료입니다.", "Data for a different species from Korean cheonnyeoncho."),
    (169272, "aehobakleaf", "related_species_reference", "leaves", "호박류(Cucurbita spp.) 생잎, 종 미특정",
     "Pumpkin (Cucurbita spp.) leaves, raw; species not specified", "애호박(C. moschata)으로 특정되지 않은 호박속 자료입니다.", "Genus-level data, not specific to C. moschata."),
    (169272, "pumpkinleaf", "related_species_reference", "leaves", "호박류(Cucurbita spp.) 생잎, 종 미특정",
     "Pumpkin (Cucurbita spp.) leaves, raw; species not specified", "종이 특정되지 않은 호박속 자료입니다.", "Genus-level data; the species is not specified."),
]
RDA = [
    ("R106-198007801-0000", "aehobakleaf", "related_species_reference", "Cucurbita sp. (species not stated by source)", "leaves", "국가표준식품성분표 호박잎 생것. 원자료에 호박 종이 표기되지 않음",
     "Korean Standard Food Composition Table: pumpkin leaves, raw; the source does not state the Cucurbita species", "애호박(C. moschata) 잎으로 특정되지 않습니다.", "Not specific to C. moschata leaves."),
    ("R106-198007801-0000", "pumpkinleaf", "related_species_reference", "Cucurbita sp. (species not stated by source)", "leaves", "국가표준식품성분표 호박잎 생것. 원자료에 호박 종이 표기되지 않음",
     "Korean Standard Food Composition Table: pumpkin leaves, raw; the source does not state the Cucurbita species", "", ""),
    ("R106-170000001-0000", "broadleafplantain", "related_species_reference", "Plantago asiatica (Korean 질경이; species from korea_taxon_mapping_v1)", "whole edible plant (leaves)", "국가표준식품성분표 질경이(Plantago asiatica) 생것. 왕질경이(Plantago major)와 다른 종",
     "Korean Standard Food Composition Table: Asian plantain (Plantago asiatica), raw; a different species from broadleaf plantain (Plantago major)", "같은 속 다른 종의 자료입니다.", "Data for a different species of the same genus."),
    ("R106-123000001-0000", "commonmallow", "related_species_reference", "Malva verticillata (Korean 아욱)", "leaves and young stems", "국가표준식품성분표 아욱(Malva verticillata) 생것. 말바(Malva sylvestris)와 다른 종",
     "Korean Standard Food Composition Table: Chinese mallow (Malva verticillata), raw; a different species from common mallow (Malva sylvestris)", "같은 속 다른 종의 자료입니다.", "Data for a different species of the same genus."),
    ("R106-159000001-0000", "hosta", "related_species_reference", "Hosta sp. (Korean 비비추/이밥추; species not stated by source)", "leaves", "국가표준식품성분표 비비추(이밥추) 생것. 비비추속 한 종의 자료이며 종명 미표기",
     "Korean Standard Food Composition Table: hosta (bibichu/ibapchu), raw; one Hosta food, species not stated", "비비추속 전체의 대표값이 아닙니다.", "Not representative of all Hosta species."),
    ("R106-211002701-0000", "buckwheatleaf", "related_part_reference", "Fagopyrum esculentum (Korean 메밀)", "sprouts", "국가표준식품성분표 메밀 싹 생것. 다 자란 잎이 아닌 새싹",
     "Korean Standard Food Composition Table: buckwheat sprouts, raw; sprouts, not mature leaves",
     "새싹 자료이며, 원자료의 식이섬유(3.6g)가 차감법 탄수화물(1.9g)보다 커 내부 일관성이 낮습니다.",
     "Sprout data; the source lists dietary fibre (3.6 g) above carbohydrate by difference (1.9 g), an internal inconsistency."),
    ("R106-197002701-0000", "sunflowerleaf", "related_part_reference", "Helianthus annuus (Korean 해바라기)", "sprouts", "국가표준식품성분표 해바라기 싹 생것. 다 자란 잎이 아닌 새싹",
     "Korean Standard Food Composition Table: sunflower sprouts, raw; sprouts, not mature leaves", "새싹 자료입니다.", "Sprout data."),
]
RDA_COLS = {"수분(g)": "water_g", "단백질(g)": "protein_g", "지방(g)": "fat_g", "회분(g)": "ash_g", "탄수화물(g)": "carbohydrate_g",
            "식이섬유(g)": "fiber_g", "칼슘(mg)": "calcium_mg", "철(mg)": "iron_mg", "인(mg)": "phosphorus_mg", "칼륨(mg)": "potassium_mg",
            "나트륨(mg)": "sodium_mg", "비타민 C(mg)": "vitamin_c_mg"}
USDA_NAMES = {"Water": "water_g", "Protein": "protein_g", "Total lipid (fat)": "fat_g", "Carbohydrate, by difference": "carbohydrate_g",
              "Fiber, total dietary": "fiber_g", "Ash": "ash_g", "Calcium, Ca": "calcium_mg", "Phosphorus, P": "phosphorus_mg",
              "Magnesium, Mg": "magnesium_mg", "Potassium, K": "potassium_mg", "Sodium, Na": "sodium_mg", "Iron, Fe": "iron_mg",
              "Vitamin C, total ascorbic acid": "vitamin_c_mg"}


def note(base_ko, base_en, extra_ko, extra_en):
    return (" ".join(x for x in (extra_ko, base_ko) if x), " ".join(x for x in (extra_en, base_en) if x))


def from_feedipedia(cache, node, pid, tier, sci, part, sko, sen, cko, cen):
    page = (cache / f"feedipedia_{node}.html").read_text(encoding="utf-8", errors="replace")
    rows, title = V.parse_feedipedia(page)
    nutrients, counts, units = {}, {}, {}
    for key, lab in V.FEEDIPEDIA_LABELS.items():
        if lab in rows:
            avg, nb = rows[lab]
            nutrients[key] = avg
            units[key] = DM_UNITS[key]
            counts[key] = nb if isinstance(nb, int) else "equation"
    ko, en = note(DM_NOTE_KO, DM_NOTE_EN, cko, cen)
    return {"reference_id": f"feedipedia-{node}-{pid}-{TODAY.replace('-', '')}", "plant_id": pid, "scientific_name": sci,
            "source_name": f"Feedipedia — {title}", "source_id": str(node), "source_url": f"https://www.feedipedia.org/node/{node}",
            "analyzed_part": part, "preparation_state": "fresh sample; nutrients on dry-matter basis",
            "basis": "dry matter (DM); dry matter % as fed; protein/fibre % DM; minerals g/kg DM", "nutrients": nutrients,
            "nutrient_units": units, "sample_counts": counts, "display_tier": tier, "reference_scope_ko": sko, "reference_scope_en": sen,
            "display_note_ko": ko, "display_note_en": en, "source_verification": f"feedipedia_table_parsed_{TODAY}", **COMMON}


def from_mext(cache, code, pid, tier, part, sko, sen, cko, cen):
    vals, name, sci = V.parse_mext((cache / f"mext_{code}.html").read_text(encoding="utf-8", errors="replace"))
    ko, en = note(FRESH_NOTE_KO, FRESH_NOTE_EN, cko, cen)
    return {"reference_id": f"mext-{code}-{pid}-{TODAY.replace('-', '')}", "plant_id": pid, "scientific_name": sci,
            "source_name": "MEXT Standard Tables of Food Composition in Japan 2023 — " + name, "source_id": code,
            "source_url": f"https://fooddb.mext.go.jp/details/details.pl?ITEM_NO=6_{code}_7", "analyzed_part": part,
            "preparation_state": "raw", "basis": "per 100 g edible portion, raw",
            "nutrients": {k: v for k, v in vals.items() if v is not None}, "nutrient_units": {k: FRESH_UNITS[k] for k, v in vals.items() if v is not None},
            "display_tier": tier, "reference_scope_ko": sko, "reference_scope_en": sen, "display_note_ko": ko, "display_note_en": en,
            "source_verification": f"mext_item_page_parsed_{TODAY}", **COMMON}


def from_usda(foods, fdc, pid, tier, part, sko, sen, cko, cen):
    f = foods[fdc]
    vals = {}
    for n in f["foodNutrients"]:
        k = USDA_NAMES.get(n["nutrient"]["name"])
        if k and n.get("amount") is not None:
            vals[k] = n["amount"]
    ko, en = note(FRESH_NOTE_KO, FRESH_NOTE_EN, cko, cen)
    return {"reference_id": f"usda-{fdc}-{pid}-{TODAY.replace('-', '')}", "plant_id": pid, "scientific_name": f.get("scientificName"),
            "source_name": f"USDA FoodData Central SR Legacy 2018-04 — {f['description']}", "source_id": f"FDC {fdc} (NDB {f.get('ndbNumber')})",
            "source_url": f"https://fdc.nal.usda.gov/food-details/{fdc}/nutrients", "analyzed_part": part, "preparation_state": "raw",
            "basis": "per 100 g edible portion, raw", "nutrients": vals, "nutrient_units": {k: FRESH_UNITS[k] for k in vals},
            "display_tier": tier, "reference_scope_ko": sko, "reference_scope_en": sen, "display_note_ko": ko, "display_note_en": en,
            "source_verification": f"usda_sr_legacy_json_parsed_{TODAY}", **COMMON}


def from_rda(rows, code, pid, tier, sci, part, sko, sen, cko, cen):
    d = rows[code]
    vals = {v: float(d[k]) for k, v in RDA_COLS.items() if d.get(k, "").strip() not in ("", "-")}
    ko, en = note(FRESH_NOTE_KO, FRESH_NOTE_EN, cko, cen)
    return {"reference_id": f"rda-{code.lower()}-{pid}-{TODAY.replace('-', '')}", "plant_id": pid, "scientific_name": sci,
            "source_name": f"농촌진흥청 국가표준식품성분표(통합식품영양성분정보 원재료성식품) — {d['식품명']}", "source_id": code,
            "source_url": "https://www.data.go.kr/data/15100065/standard.do", "analyzed_part": part, "preparation_state": "raw",
            "basis": "per 100 g edible portion, raw", "nutrients": vals, "nutrient_units": {k: FRESH_UNITS[k] for k in vals},
            "source_data_generation": {"method": d.get("데이터생성방법명"), "generated": d.get("데이터생성일자"), "reference_date": d.get("데이터기준일자")},
            "display_tier": tier, "reference_scope_ko": sko, "reference_scope_en": sen, "display_note_ko": ko, "display_note_en": en,
            "source_verification": f"rda_csv_2025-12-23_parsed_{TODAY}", **COMMON}


def ifct_minerals(pdf):
    """C030 Pumpkin leaves, tender: mineral rows from IFCT 2017 pages 159-160 (column-aligned by x position)."""
    import pymupdf
    doc = pymupdf.open(pdf)
    out = {}
    for pno, want in ((158, {"CA": "calcium_mg", "FE": "iron_mg"}), (159, {"MG": "magnesium_mg", "P": "phosphorus_mg", "K": "potassium_mg", "NA": "sodium_mg", "ZN": "zinc_mg"})):
        ws = doc[pno].get_text("words")
        first = next(w for w in ws if w[4] in ("AL", "MG") and w[1] > 50)
        hyc = (first[1] + first[3]) / 2
        hdr = [w for w in ws if abs((w[1] + w[3]) / 2 - hyc) < 1.5]
        code = next(w for w in ws if w[4] == "C030")
        yc = (code[1] + code[3]) / 2
        for v in [w for w in ws if abs((w[1] + w[3]) / 2 - yc) < 1.5 and w[0] > code[2] + 15]:
            h = min(hdr, key=lambda h: abs((h[0] + h[2]) / 2 - (v[0] + v[2]) / 2))
            if h[4] in want and abs((h[0] + h[2]) / 2 - (v[0] + v[2]) / 2) < 3:
                out[want[h[4]]] = float(v[4].split("±")[0])
    return out


def pmc_rose_marigold(xml):
    """PMC8472405: macroelements (mg/kg FM) and crude protein (g/kg FM) for Rosa and Tagetes patula."""
    import html as H
    x = Path(xml).read_text(encoding="utf-8")
    res = {"Rosa": {}, "Tagetes patula": {}}
    for m in re.finditer(r"<table-wrap\b.*?</table-wrap>", x, re.S):
        t = m.group(0)
        rows = [[H.unescape(re.sub(r"<[^>]+>", "", c)).strip() for c in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", r, re.S)] for r in re.findall(r"<tr[^>]*>(.*?)</tr>", t, re.S)]
        head = rows[0] if rows else []
        for r in rows[1:]:
            if r and r[0] in res:
                for name, val in zip(head[1:], r[1:]):
                    m2 = re.match(r"^\s*([0-9][0-9,]*(?:\.[0-9]+)?)\s*±", val)
                    if m2:   # only "mean ± SD" cells of the composition tables
                        res[r[0]][name] = float(m2.group(1).replace(",", ""))
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True)
    ap.add_argument("--usda", required=True)
    ap.add_argument("--rda", required=True)
    ap.add_argument("--ifct", required=True)
    ap.add_argument("--pmc-8472405", dest="pmc", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    cache = Path(a.cache)
    foods = {f["fdcId"]: f for f in json.loads(Path(a.usda).read_text(encoding="utf-8"))["SRLegacyFoods"]}
    rrows = list(csv.reader(io.StringIO(Path(a.rda).read_bytes().decode("utf-8-sig"))))
    rda = {r[0]: dict(zip(rrows[0], r)) for r in rrows[1:]}
    new = [from_feedipedia(cache, *c) for c in FEEDIPEDIA] + [from_mext(cache, *c) for c in MEXT] + \
          [from_usda(foods, *c) for c in USDA] + [from_rda(rda, *c) for c in RDA]

    path = ROOT / "data/plant_nutrition_reference_v1.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    by_id = {r["reference_id"]: r for r in doc["records"]}

    # completeness fixes on existing records, from the same original sources
    pm = pmc_rose_marigold(a.pmc)
    rose, mari = by_id["pmc8472405-rosa-gloria-dei-flowers-20261010"], by_id["pmc8472405-tagetes-patula-antiqua-orange-20261010"]
    for rec, src in ((rose, pm["Rosa"]), (mari, pm["Tagetes patula"])):
        for name, key, unit in (("Crude Protein", "crude_protein_g_per_kg_fresh", "g/kg fresh mass"), ("Phosphorus", "phosphorus_mg_per_kg_fresh", "mg/kg fresh mass"),
                                ("Potassium", "potassium_mg_per_kg_fresh", "mg/kg fresh mass"), ("Calcium", "calcium_mg_per_kg_fresh", "mg/kg fresh mass"),
                                ("Magnesium", "magnesium_mg_per_kg_fresh", "mg/kg fresh mass"), ("Sodium", "sodium_mg_per_kg_fresh", "mg/kg fresh mass")):
            if name in src:
                if key in rec["nutrients"] and abs(rec["nutrients"][key] - src[name]) > 1e-9:
                    sys.exit(f"{rec['reference_id']}: existing {key} {rec['nutrients'][key]} differs from source {src[name]}")
                rec["nutrients"][key] = src[name]
                rec["nutrient_units"][key] = unit
    rose["basis"] = "dry matter % of fresh flower mass; crude protein g/kg fresh mass; minerals mg/kg fresh mass; total phenolics g GAE/kg and total flavonoids g RE/kg fresh mass"
    pk = by_id["ifct2017-c030-pumpkinleaf-20261010"]
    for k, v in ifct_minerals(a.ifct).items():
        pk["nutrients"][k] = v
        pk["nutrient_units"][k] = "mg/100g fresh"
    pk["source_id"] = "IFCT 2017 C030 Tables 1 (proximate) and 9 (minerals)"
    ch = by_id["ejmp2024-stellaria-media-fresh-leaves-20261010"]
    ch["quality_flags"] = ["internal_inconsistency: crude fibre 6.5 g/100 g fresh is about 48% of dry matter; dried-sample Ca and protein do not scale with the moisture loss (Table 1)"]

    for r in new:
        by_id[r["reference_id"]] = r
    doc["records"] = list(by_id.values())
    doc["coverage"] = {"reference_records": len(doc["records"]), "distinct_plants": len({r["plant_id"] for r in doc["records"]}),
                       "notice": doc.get("coverage", {}).get("notice", "")}
    doc["display_policy"]["related_cultivar_reference"] = "Show the cultivar name and warn that cultivars differ."
    if a.dry_run:
        print(json.dumps(new[:2], ensure_ascii=False, indent=1))
        print(len(new), "new records;", doc["coverage"])
        return
    path.write_bytes((json.dumps(doc, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))   # repo style: 2 spaces, LF
    print(f"wrote {len(new)} new reference records; {doc['coverage']}")


if __name__ == "__main__":
    main()
