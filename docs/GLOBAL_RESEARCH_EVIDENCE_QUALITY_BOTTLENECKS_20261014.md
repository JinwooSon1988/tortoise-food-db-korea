# Evidence-quality bottleneck audit — 2026-10-14

Source: PR #304 `data/research/tortoise_plant_evidence_v1.json` (169 records). These are data-field counts, **not** an independent re-reading of original papers.

| Directness field | Records | What it supports |
|---|---:|---|
| `primary_study_read` | 46 | Research data reports a primary study read; still review the original methods and limits before publication |
| `reported_in_account_primary_not_read` | 102 | Secondary account reports primary findings; **do not present as independently checked primary evidence** |
| `statement_of_the_source_read` | 21 | Statement directly read in the consulted source; **not automatically a primary experiment** |
| **Total** | **169** | **No automatic grade or safety approval** |

Of the 169 records, **104** have plant-part text matching `not stated`, `unknown` or `unspecified`; this is a lexical audit of the research field, not a determination that the entire underlying literature lacks part information. **7** records are flagged `is_negative_record`; avoidance or rejection is not proof of toxicity.

## Priorities for Claude's next research pass

1. **Primary-reference recovery (102 records):** trace the original cited paper and verify the actual tortoise species, plant identity, part, method and context; keep `reported_in_account_primary_not_read` until the original is examined.
2. **Plant-part recovery (104 records):** check original tables and methods for leaf, flower, stem, fruit, pad or whole-plant distinction. Preserve `not stated` where the source truly omits it; do not infer a part from the public plant-page name.
3. **Negative observations (7 records):** distinguish observed avoidance, non-selection and documented toxicity; do not automatically classify any as poisonous or safe.
4. **Cross-species applicability:** maintain source species; evidence for *Testudo hermanni*, *Centrochelys sulcata* or *Stigmochelys pardalis* does not automatically validate all tortoises.
5. **Publication:** retain research-only state until source checks, toxicology, nutritional context and taxon-specific limits are complete.

This document changes neither public plant data nor feeding grades.
