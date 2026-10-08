# Global nutrition evidence intake protocol — 2026-10-08

## Baseline and scope
Repository audit baseline: 182 public plants; 49 verified nutrition mappings; 133 held (26.9% verified). This is nutrition-record coverage, **not** feeding safety coverage. Recalculate after each intake batch rather than treating this snapshot as live.

## Worldwide discovery matrix (sources to investigate, not records already verified)
- Global: FAO/INFOODS food composition resources; peer-reviewed botany, food chemistry, veterinary and field-ecology literature.
- Europe: EuroFIR network and national food composition databases; UK CoFID; Finnish Fineli; Danish Frida; French Ciqual; German BLS; Dutch NEVO; Swiss Food Composition Database.
- Asia: Korea RDA and other official datasets; Japan Standard Tables of Food Composition; China Food Composition Tables; Indian Food Composition Tables; ASEAN national tables.
- Americas: USDA FoodData Central; Canadian Nutrient File; Latin American national food composition datasets and LATINFOODS.
- Africa: AFROFOODS and national food composition tables.
- Oceania: Australian Food Composition Database and New Zealand FOODfiles.

These are **discovery leads**. Do not assume coverage, current accessibility, open licensing, or an exact plant record exists. Record the source URL, edition, access date, and reuse permissions.

## Identity and acceptance gate
1. Resolve accepted botanical taxon and synonyms against authoritative taxonomy (e.g., Kew POWO/WFO), and preserve original source taxon.
2. Match food record at the finest supported level: species, cultivar/subspecies if material, plant part, growth stage, raw/dried/cooked state, and geographical provenance where relevant.
3. Record official/peer-reviewed source title, URL/DOI, record identifier, publication or database edition, units, denominator (per 100 g fresh weight vs dry matter), analytical vs imputed status, and any uncertainty.
4. Never transfer fruit composition to leaves, genus averages to an unspecified species, or cooked/dried values to raw foods. Do not silently convert dry to fresh weight without measured moisture and an explicit transformation record.
5. Keep nutrient concentration evidence separate from tortoise feeding safety and animal-specific applicability. A composition paper does not establish safe dose or frequency.
6. If any critical identity or analytical field is absent, retain hold with explicit reason; do not create numeric placeholders or promote a verdict.
7. Log rejected as well as accepted candidates, including why a seemingly close record is not transferable.

## Batch workflow
- Prioritize the 133 held plants by user search relevance and likelihood of an exact-match record, not by ease of artificially raising coverage.
- Batch 10–20 candidates: worldwide search log -> taxon/part/state reconciliation -> source verification -> data edit -> coverage regeneration -> QA -> independent review.
- Track `verified_before`, `verified_after`, `held_before`, `held_after`, newly published record IDs, rejected IDs and reasons. Avoid double-counting variants or synonyms.
- After existing records are reviewed, intake new plant candidates in a separate unpublished queue with botanical identity and evidence-distance review. No automatic feeding verdicts.

## Division of labor
Claude: research and nutrition-related data files and their validators. ChatGPT: UI generator, evidence presentation, integration QA, deployment review. Neither edits the other's owned files during a batch. Report Git commit SHAs and failed gates.

## Completion criteria
Evidence is source-traceable, plant identity and part/state exact, safety conclusions not inferred from nutrient tables, hold reasons explicit, all applicable automated tests pass, and generated pages are verified separately.
