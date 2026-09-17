# Evidence matrix v5.6

## Purpose
This matrix is the audit layer between raw sources and public feeding guidance. It prevents nutrition composition, wild feeding observations, husbandry surveys, and general chelonian reviews from being collapsed into a single unsupported feeding verdict.

## Evidence axes
1. Identity: exact scientific taxon, Korean retail/common name, edible part, preparation state.
2. Korean composition: RDA/NICS National Standard Food Composition DB 10.4. Record food code, food name, raw/cooked/dried state, edible part, source/version and observed date. Composition is descriptive and must not change feeding verdict by itself.
3. International composition: USDA FoodData Central, retained as a separate source rather than overwriting RDA values.
4. Direct feeding ecology: exact subspecies > species > Testudo genus > husbandry group > tortoise general.
5. Nutrition/physiology: controlled feeding/digestibility studies and clinical reviews. These can explain mechanisms and limitations but must not be converted into plant-specific safety claims without direct support.
6. Specialist husbandry: supplementary context only; label source and scope.

## Interpretation contract
- Wild feeding occurrence does not equal a captive diet percentage or unlimited feeding recommendation.
- Human food-composition data do not establish tortoise safety, frequency, or suitability.
- A study on another Testudo species is not an exact-species result.
- Exact-subspecies physiological data are not automatically plant-specific feeding evidence.
- Missing evidence is displayed as a gap, not silently filled by inference.
- Every public claim should be traceable to a source identifier and include what the source does **not** support.

## Verified source anchors
| ID | Type | Taxon/scope | Supports | Does not support |
|---|---|---|---|---|
| RDA_NICS_FCDB_10_4 | official composition DB | Korean foods | Korean food composition when an exact food/part/state match is verified | tortoise safety, frequency, ideal ratios |
| USDA_FDC | official composition DB | human foods | separate international composition reference when identity/part/state match | tortoise safety or feeding verdict |
| PMID_29609473 | captive husbandry survey | Testudo spp.; 1,075 respondents | association of husbandry/diet regime with pyramidal growth; survey reports >80% grasses/weeds as optimal summer diet category | safety/frequency of an individual plant; causation from a controlled trial |
| PMID_20850560 | controlled comparative digestion study | herbivorous reptiles incl. T. graeca, T. hermanni | food intake, retention, digestibility and gut-capacity physiology across body mass | individual plant safety or a captive recipe |
| PMID_37661549 | clinical review | Chelonia/tortoises | practical nutrition context, feeding ecology, digestive physiology, captive diet categories | exact Ibera plant verdict unless separately sourced |
| slimani2006 | wild feeding ecology | T. graeca graeca, Morocco | direct wild feeding ecology including reported plant taxa | Korean common-name identity mapping or captive percentages |
| iftime_ibera_dobrogea_2012 | wild feeding ecology | T. graeca ibera, Dobrogea | direct Ibera wild diet observations and reported occurrence classes | captive diet percentages or unlimited use |
| mitrevichin_ibera_bulgaria_2023 | field observations | T. graeca ibera, Bulgaria | direct Ibera observations including Cichorium intybus, Taraxacum sp., Medicago sp. and others | quantitative captive frequency/ratio |

## 69-food audit columns
For every master food ID record: `food_id`, `ko_name`, `scientific_name`, `identity_scope`, `edible_part`, `state`, `rda_10_4_status`, `rda_food_code`, `rda_match_note`, `usda_status`, `usda_fdc_id`, `exact_ibera_evidence`, `species_evidence`, `testudo_evidence`, `tortoise_general_evidence`, `composition_only_evidence`, `public_verdict`, `applicability`, `evidence_grade`, `supports`, `does_not_support`, `gap`, `last_verified_at`.

## Priority audit queue
Start with foods most likely to be used by Korean keepers and/or already carrying stronger public guidance: chicory, romaine, dandelion, plantain, sowthistle, clover, alfalfa, mallow, mulberry leaf, kale, chard, watercress, bok choy, napa cabbage, mustard greens, turnip greens, collard greens, arugula, parsley, cilantro, spinach, beet greens, radicchio, endive, broccoli leaf, cauliflower leaf, hibiscus leaf/flower, fig leaf, opuntia and sedum.

## RDA integration gate
RDA 10.4 data may enter the public nutrition registry only after food-name/part/state reconciliation. If scientific identity is absent or ambiguous, use an independent official identity source before mapping to the master taxon. Never replace a USDA record merely because an RDA name looks similar; preserve both provenance chains.

## Public-page target
A mature plant page should answer, in order: what plant is this; can the identity be trusted; what is the current feeding level; what evidence is direct to Ibera/Testudo; what Korean and USDA composition data say; what those data cannot prove; how the item functions in a mixed diet; what recent feeding history suggests checking next.