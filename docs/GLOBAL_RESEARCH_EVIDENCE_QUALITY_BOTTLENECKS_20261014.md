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

## Source-check status is not the same as directness classification

The 46/102/21 counts above are a snapshot of the **research JSON's evidence_directness fields**, not a count of records independently verified by this review. The separate original-PDF check of the Hermann's tortoise account is documented in `docs/GLOBAL_RESEARCH_EXISTING_SPECIES_REVIEW_20261014.md`; it verifies the account's **fruit** wording for *Ficus carica*, but **does not** upgrade the underlying cited field study to a read primary source.

When independent source checks are added, record the original PDF URL, printed page/section, exact plant part and tortoise species, what the source actually asserts, and whether the underlying primary reference was opened. Never silently relabel `reported_in_account_primary_not_read` as `primary_study_read` solely because an account PDF was read.
