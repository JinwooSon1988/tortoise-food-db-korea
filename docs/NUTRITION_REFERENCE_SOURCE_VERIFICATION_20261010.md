# Nutrition reference records: original-source verification and gap batch (2026-10-10)

Scope: `data/plant_nutrition_reference_v1.json` (REFERENCE tier only). Verified official values in
`data/plant_nutrition_v56.json` / `data/rda_food_composition_v56.json` and all feeding verdicts are unchanged.

## 1. Coverage (published plants, recomputed with `node scripts/audit_nutrition_coverage.mjs`)

| | before (main 4ae6c48f) | after |
|---|---|---|
| Verified official, exact plant/part/state | 63 | 63 |
| Reference records only | 25 | 49 |
| No linked numeric record | 94 | 70 |
| Reference records / plants with references | 39 / 28 | 72 / 52 |

No plant was promoted to VERIFIED: none of the new sources is the exact species, part and raw state of the master record.

## 2. The 39 existing reference records against their originals

All 39 match their original sources value by value; no number was wrong.

- 31 checked automatically with `scripts/verify_nutrition_reference_sources_v1.py` (Feedipedia node pages including
  per-nutrient sample counts, MEXT item pages, Matvaretabellen food pages, the JIRCAS page).
- 8 checked by hand: PMC10909542 Table 1 (ryegrass cut 2/4), PMC8472405 Tables 4–6 (marigold, rose), PMC6268292
  Tables 2, 3, 6 (pansy), PMC4137549 Table 3 (fennel leaves), EJMP 1177 revised manuscript Table 1 (chickweed),
  IFCT 2017 page 45 row C030 (pumpkin leaves; rows reconstructed from PDF word coordinates because the text layer
  misaligns names and values on that page).

Findings recorded instead of silently fixed:

| record | finding | action |
|---|---|---|
| chickweed `ejmp2024-…` | values match the source, but the source is internally inconsistent: crude fibre 6.5 g/100 g fresh ≈ 48 % of dry matter; dried-sample Ca (×11) and protein (×4) do not scale with the moisture loss (×7) | kept REFERENCE, `quality_flags` added |
| waterdropwort `international-20261010-2` (JIRCAS) | matches the page, but JIRCAS is a secondary compilation with no cited analysis | noted here; kept REFERENCE |
| fennel `barros2010-…` | matches the 2014 review's reproduction of Table 3; the 2010 original is not openly accessible | noted (already stated in the record) |
| rose, marigold | the same paper reports crude protein and five macro-minerals (rose) and sodium (marigold) that had not been transcribed | added from Tables 4 and 6 |
| pumpkin leaves IFCT C030 | the record had proximates only; IFCT 2017 mineral tables (pages 159–160) give Ca 271, P 64.54, Mg 84.21, K 423, Na 12.20, Fe 5.58, Zn 0.90 mg/100 g | added; `source_id` updated |

## 3. New REFERENCE records (33 records, 24 plants that previously had none)

Rules: same plant part of a related taxon, a related part of the same taxon (stems + leaves, aerial forage,
sprouts), or a dry-matter forage table. Fruit, seed and grain values are never linked to leaf or flower plants
(strawberry/apple/cucumber/grain records in the hold list stay unlinked). Units and basis are kept as published;
dry-matter values are not converted. Each record has Korean and English scope and caution text.

| plant | source(s) | why REFERENCE, not VERIFIED |
|---|---|---|
| aehobakleaf | RDA R106-198007801-0000 호박_잎_생것; USDA FDC 169272 | species not stated (RDA) / Cucurbita spp. (USDA) |
| pumpkinleaf (added) | RDA R106-198007801-0000; USDA FDC 169272 | genus-level master; sources disagree (Ca 39–285 mg/100 g), kept separate |
| pumpkinflower | USDA FDC 169270 Pumpkin flowers, raw | Cucurbita spp.; no Korean taxon mapping |
| dock | USDA FDC 170076 Dock, raw | Rumex spp., not R. crispus |
| grapevineleaf | USDA FDC 168575; Feedipedia 12132 | Vitis vinifera, not V. amurensis |
| borage | USDA FDC 170481 | part not stated by USDA |
| pricklypear | USDA FDC 168571 Nopales; Feedipedia 11595 | Nopalea cochenillifera / Opuntia ficus-indica, not confirmed as 천년초 |
| broadleafplantain | RDA R106-170000001-0000 질경이 | Plantago asiatica, not P. major |
| commonmallow | RDA R106-123000001-0000 아욱 | Malva verticillata, not M. sylvestris |
| hosta | RDA R106-159000001-0000 비비추(이밥추) | one Hosta food, species not stated; master is genus-level |
| buckwheatleaf | RDA R106-211002701-0000 메밀 싹; Feedipedia 25609 | sprouts / aerial part; RDA row lists fibre (3.6 g) above carbohydrate (1.9 g) — flagged in the note |
| sunflowerleaf | RDA R106-197002701-0000 해바라기 싹; Feedipedia 12667 | sprouts / forage |
| celeryleaf | MEXT 06075 キンサイ 茎葉; Feedipedia 11954 | leaf-celery variety, stems + leaves / n = 1–2 |
| cornleaf | Feedipedia 22237 Maize leaves, fresh | dry-matter basis |
| comfrey | Feedipedia 12540 Russian comfrey | S. × uplandicum, not S. officinale |
| melonleaf, watermelonleaf | Feedipedia 12324, 12741 | aerial part (leaves + stems), n = 1 |
| wheatleaf, wheatgrass | Feedipedia 12761 Wheat forage, fresh | forage stage, not young sprouts or leaf-only |
| barleyleaf, barleygrass | Feedipedia 11831 Barley, aerial part, fresh | as above |
| oatleaf, oatgrass | Feedipedia 12390 Oat forage, fresh | as above |
| clover | Feedipedia 12762 (T. repens), 12508 (T. pratense) | genus-level master; one species each |
| vicia_cracca | Feedipedia 12012 | Vicia sativa, not V. cracca |

Reproduce: `scripts/build_nutrition_reference_batch_20261010.py` (reads the cached original files; see its docstring
for download routes). Feedipedia pages were fetched at the site's 10 s crawl delay; PMC articles through NCBI
E-utilities (PMC HTML disallows crawling); the EJMP journal site is behind a Cloudflare challenge and was not accessed.

## 4. Still unresolved (70 plants)

Hold reasons in `data/nutrition_hold_list_v1.json` remain valid for these; examples: genus-level ornamentals and wild
genera with no composition data (Pelargonium, Dahlia, Zinnia, Petunia, Coreopsis, Astilbe, Primula, Monarda,
Hieracium, Crepis, Leontodon, Tragopogon, Oenothera, tree genera Tilia/Corylus/Betula/Ulmus/Acer/Populus/Crataegus),
herbs available only dried (sage, oregano — a display tier for processed state would be needed), fruit-only
records for leaf plants (strawberry, raspberry, apple, plum, peach, kiwi, cucumber), and species with no record
found (Hibiscus syriacus leaves/flowers, lavender, chamomile, echinacea, yarrow, lemon balm, marshmallow, hollyhock,
henbit, daisy, catsear, Kentucky bluegrass, tall fescue, ginkgo leaves, Phaseolus vulgaris leaves and others).
Weeping-willow leaves exist only as a dried-leaf table (Feedipedia 12748) and were not linked.

## 5. Checks

- `scripts/audit_nutrition_references.py`: now accepts the cultivar tier and requires an explicit denominator for every
  nutrient unit and for the basis (per 100 g, per kg fresh mass, % DM …). The previous rule rejected correct per-kg
  journal units; a fix proposed on `audit/nutrition-reference-integrity-20261010` put the new condition inside a
  comment (literal `\n`), which would have disabled the check, so it was not used.
- `audit_nutrition_reference_queue`, `audit_nutrition_consistency`, `qa_nutrition_hold_list_v1`, `audit_nutrition_v56`,
  `qa_nutrition_part_state_v1`, `qa_nutrition_dm_basis_v1`, `qa_nutrition_coverage_queue_v1`: pass.
- `data/nutrition_coverage_audit_v1.json` regenerated (`build_nutrition_coverage_audit_v1.py`).
