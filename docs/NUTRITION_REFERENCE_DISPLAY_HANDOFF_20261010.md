# Nutrition reference-only display: non-UI handoff (2026-10-10)

## Current audit (published plants only)

- Published: 182
- Official verified or exact-match RDA: 63
- Reference-only with recorded nutrient values: 25
- No linked numeric nutrition record: 94

These are **data linkage tiers**, not tortoise feeding safety verdicts. A reference-only plant can still correctly show 'no verified exact-match nutrition values', but must not be visually indistinguishable from a plant with no linked nutrition records.

## Safe UI implementation contract (for Claude AFTER current UI task)

Do not change any working routes, history, back/home buttons, filters, locale switching, or plant verdicts. Read `data/plant_nutrition_reference_v1.json` as a *separate reference-only source*. For each published plant ID:

1. If a verified exact-match nutrient record exists, show verified values under the verified heading. Reference records, if displayed, must remain separately labeled.
2. Otherwise if reference-only records with nonempty `nutrients` exist, show `검증된 동일 부위·상태 영양자료 없음` **and** a distinct `관련 영양 참고자료` section containing original numeric values, `reference_scope_ko` / `analyzed_part`, `preparation_state`, `basis`, `source_name`, `source_id` when present, `source_url`, and `display_note_ko`. State clearly that this is not an exact plant-part match and does not prove safety or determine the feeding grade.
3. Otherwise show `연결된 영양자료 없음`. Do not fabricate zeros or imply that no published study exists.

Preserve original units and fresh/dry-matter basis. Never compare dry-matter numbers directly with fresh-weight per-100g numbers; never infer a calcium-to-phosphorus ratio from mismatched basis or missing values. No data changes are authorized by this note.

## QA acceptance criteria

- Every reference-only plant shows at least one actual reference record and its source; none shows only the same empty-state text as an unlinked plant.
- No unlinked plant gets a reference value via common-name or synonym matching alone.
- Verified values never get overwritten by reference-only values.
- Korean and English UI share the same data; labels and notes must be properly translated, preserving scientific names, numbers, units, and source URLs.
- Back/home, English navigation, search, and all existing behavior remain unchanged.

## Reference-only published plant IDs (25)

- `lettuce` — 상추; 1 record(s); e.g. Norwegian Food Composition Table — Matvaretabellen; 상추(Lactuca sativa) 생잎, 품종 미지정, 생체 100g 기준
- `figleaf` — 무화과잎; 1 record(s); e.g. Feedipedia — Animal Feed Resources Information System (INRAE, CIRAD, AFZ, FAO); Ficus carica leaf, fresh 사료 성분 (건조물 기준)
- `mint` — 민트; 1 record(s); e.g. Norwegian Food Composition Table — Matvaretabellen; 민트류(Mentha L.), 생허브의 잎 및 소량의 기타 부위, 생체 100g
- `alfalfa` — 알팔파; 2 record(s); e.g. Feedipedia — Animal Feed Resources Information System (INRAE, CIRAD, AFZ, FAO); Medicago sativa aerial part, fresh 사료 성분 (건조물 기준)
- `chickweed` — 별꽃; 1 record(s); e.g. European Journal of Medicinal Plants (2024), Effects of Various Drying Methods on the Proximate Composition and Antioxidant Activities of Stellaria media Leaves; 별꽃(Stellaria media)의 생잎(FL) 시료, 생체 100g 기준. 줄기·꽃을 포함한 식물 전체와 구분
- `pumpkinleaf` — 호박잎; 1 record(s); e.g. Indian Food Composition Tables 2017 — National Institute of Nutrition, ICMR; 서양호박(Cucurbita maxima)의 어린 잎, 생체 100g 기준
- `rose` — 장미꽃; 1 record(s); e.g. Mlcek et al., Foods (2021), Chemical, Nutritional and Sensory Characteristics of Six Ornamental Edible Flowers Species; 장미(Rosa) 'Gloria Dei' 품종의 개화한 꽃 시료, 생체 질량 기준; 논문에 종명과 꽃잎 단독 분석 여부가 명시되지 않음
- `timothy` — 티모시; 2 record(s); e.g. Feedipedia — Animal Feed Resources Information System (INRAE, CIRAD, AFZ, FAO); Phleum pratense aerial part, fresh 사료 성분 (건조물 기준)
- `orchard` — 오차드그라스; 2 record(s); e.g. Feedipedia — Animal Feed Resources Information System (INRAE, CIRAD, AFZ, FAO); Dactylis glomerata aerial part, fresh 사료 성분 (건조물 기준)
- `ryegrass` — 라이그라스; 2 record(s); e.g. Muhandiram et al. (2023), Food and Energy Security, Table 1; 페레니얼 라이그라스(Lolium perenne) AberMagic 품종, 2차 수확 생목초(잎 단독 아님). 수분·탄수화물·총질소의 분모가 서로 다름.
- `marigold` — 메리골드; 1 record(s); e.g. Foods (2021), Chemical, Nutritional and Sensory Characteristics of Six Ornamental Edible Flowers Species; 프렌치메리골드(Tagetes patula) 'Antiqua Orange' 품종의 개화한 꽃잎, 생체 질량 기준
- `whiteclover` — 화이트클로버; 2 record(s); e.g. Feedipedia — Animal Feed Resources Information System (INRAE, CIRAD, AFZ, FAO); Trifolium repens aerial part, fresh 사료 성분 (건조물 기준)
- `redclover` — 레드클로버; 2 record(s); e.g. Feedipedia — Animal Feed Resources Information System (INRAE, CIRAD, AFZ, FAO); Trifolium pratense aerial part, fresh 사료 성분 (건조물 기준)
- `ribwortplantain` — 창질경이; 1 record(s); e.g. Feedipedia (INRAE/CIRAD/AFZ/FAO); 창질경이 지상부, 건조물 기준 사료 성분
- `violetflower` — 제비꽃; 1 record(s); e.g. Rop et al., Molecules (2012), Edible Flowers—A New Promising Source of Mineral Elements in Human Nutrition; 팬지(Viola × wittrockiana) 'Fancy' 품종의 개화한 꽃 전체, 생체 질량 기준. 거북밥 제비꽃(Viola mandshurica)과 다른 종
- `waterdropwort` — 미나리; 2 record(s); e.g. MEXT Japan 2023; 미나리 생줄기·생잎 혼합 분석
- `fennelleaf` — 펜넬잎; 1 record(s); e.g. Barros, Carvalho & Ferreira (2010), LWT 43:814–818; numeric table reproduced in Badgujar et al. (2014), BioMed Research International, Table 3; 야생 펜넬(Foeniculum vulgare) 잎만 분리해 분석한 생체 100g 기준; 포르투갈 6월 채집 시료
- `rapeseedleaf` — 유채잎; 2 record(s); e.g. MEXT Japan 2023; 유채의 생줄기·생잎 혼합 분석
- `opuntiapad` — 손바닥선인장패드; 1 record(s); e.g. Feedipedia — Animal Feed Resources Information System (INRAE, CIRAD, AFZ, FAO); Opuntia ficus-indica cladode (pad), fresh 사료 성분 (건조물 기준)
- `bermudagrass` — 우산잔디; 2 record(s); e.g. Feedipedia — Animal Feed Resources Information System (INRAE, CIRAD, AFZ, FAO); Cynodon dactylon aerial part, fresh 사료 성분 (건조물 기준)
- `hibiscusrosa` — 하와이무궁화; 1 record(s); e.g. Feedipedia legacy table (FAO/Göhl source; revision pending); 하와이무궁화 생 지상부, 건조물 기준의 과거 사료 분석
- `sainfoin` — 샌포인; 2 record(s); e.g. Feedipedia — Animal Feed Resources Information System (INRAE, CIRAD, AFZ, FAO); Onobrychis viciifolia aerial part, fresh 사료 성분 (건조물 기준)
- `medicago_hispida` — 버클로버; 1 record(s); e.g. Feedipedia — Animal Feed Resources Information System (INRAE, CIRAD, AFZ, FAO); Medicago polymorpha L. aerial part, fresh 사료 성분 (건조물 기준)
- `erodium_botrys` — 넓은잎필라리; 1 record(s); e.g. Feedipedia — Animal Feed Resources Information System (INRAE, CIRAD, AFZ, FAO); Erodium botrys (Cav.) Bertol. aerial part, fresh 사료 성분 (건조물 기준)
- `vicia_sativa` — 살갈퀴; 2 record(s); e.g. Feedipedia — Animal Feed Resources Information System (INRAE, CIRAD, AFZ, FAO); Vicia sativa L. aerial part, fresh 사료 성분 (건조물 기준)

## Data provenance

Source registry: `data/plant_nutrition_reference_v1.json`; official registry: `data/plant_nutrition_v56.json`; RDA registry: `data/rda_food_composition_v56.json`; public membership: `data/public_assessments.json`; plant names: `data/plants.json`. Figures are a point-in-time audit and should be recomputed if these files change.
