# Unit 2 Feedipedia sample-count coverage audit — 2026-10-14

## Reproducible scope

Inspected `data/research/forage_nutrition_research_v2.json` on research branch. There are **46 total research records** with **248 nutrient entries**, of which **13 Feedipedia records** have **113 nutrient entries**. All 113 Feedipedia entries have a non-null `sample_count`. This is a **structural observation only**, not evidence that the published source shows 113 sample counts.

Feedipedia source IDs in this unit: 11897, 11723, 11650, 12513, 12881, 11865, 15787, 19894, 12063, 19702, 19703, 20402, 12640.

## Concrete source discrepancy already identified

Feedipedia 11865 (`Medicago lupulina`, fresh aerial parts) has a dry-matter value 20.9 % as fed with `sample_count=165` and calcium 16.1 g/kg DM with `sample_count=72`. Direct source-row inspection documented in `docs/FEEDIPEDIA_11865_SOURCE_ROW_AUDIT_20261014.md` found both published Nb cells blank; 165 and 72 belong to neighboring crude-protein and phosphorus rows respectively.

Because every Feedipedia nutrient entry in Unit 2 currently has a numeric sample count, the schema/pipeline may be unable to preserve a **published mean with blank Nb** without either fabricating Nb or excluding the mean. This is a hypothesis to investigate, not a confirmed pipeline defect.

## QA requirements for the Unit-2 owner

1. For each of the 13 Feedipedia pages, independently match the **exact nutrient row** and its **mean, unit, Nb cell, and calculated (*) marker**. Preserve blank Nb distinctly from zero and from missing source verification.
2. Keep a row-level audit of included, reference-only and excluded nutrients. Do not silently drop usable published means; do not present them as sample-count-verified when Nb is blank.
3. Add a regression test for Feedipedia 11865: dry matter Nb and calcium Nb must **not** be 165 or 72 respectively unless a subsequently verified source version actually supports those counts. Prefer checking the exact original row cells and source snapshot.
4. Rebuild downstream files from corrected source transcription, and verify that no feeding verdict is inferred from livestock forage composition.

**No nutritional values or feeding grades were modified by this audit.** No claim is made that the other 12 Feedipedia records contain similar errors.
