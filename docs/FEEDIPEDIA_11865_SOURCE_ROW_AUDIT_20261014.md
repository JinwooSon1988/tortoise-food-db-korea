# Feedipedia 11865 source-row audit — 2026-10-14

Source: https://www.feedipedia.org/node/11865 — *Black medic (Medicago lupulina), aerial part, fresh*.

## Direct inspection of published table

| Nutrient | Source average | Source Nb | Existing unit-2 transcription Nb | Assessment |
|---|---:|---:|---:|---|
| Dry matter | 20.9 % as fed | blank | 165 | Incorrect sample count: 165 belongs to crude protein. |
| Crude protein | 21.8 % DM | 165 | not transcribed in this record | Adjacent row explains erroneous dry-matter Nb. |
| Lignin | 4.5 % DM | 66 | 66 | Matches. |
| Calcium | 16.1 g/kg DM | blank | 72 | Incorrect sample count: 72 belongs to phosphorus. |
| Phosphorus | 3.1 g/kg DM | 72 | not transcribed in this record | Adjacent row explains erroneous calcium Nb. |
| Potassium | 15.8 g/kg DM | 5 | 5 | Matches. |

Source page explicitly says asterisk (*) means calculated average; neither dry matter nor calcium displays an asterisk in the published table, but both have blank Nb. The mean values themselves match the page; do not invent an Nb and do not represent these as sample-count-verified nutrient observations.

## Required implementation by the assigned Unit-2 research editor

1. Fix the **generating transcription/source**, not just `data/research/forage_nutrition_research_v2.json` or downstream summaries. Preserve the two means as clearly labeled reference-only data if the schema allows unknown Nb, or exclude them from the sample-count-verified layer while recording their source means and blank Nb in a transparent audit.
2. Check other rows and Feedipedia tables for accidental neighboring-row Nb assignment. Distinguish actual source Nb from a value printed in the adjacent nutrient row.
3. Regenerate dependent artifacts and run the unit-2 and global research QA. Keep all feeding verdicts unchanged.
4. Coordinate before editing the same files concurrently; no force push, PR merge or production deployment.

This is a **source audit document only**, not a correction of Unit-2 records. The source page was inspected directly on 2026-10-14; its HTML snapshot has not been committed here.
