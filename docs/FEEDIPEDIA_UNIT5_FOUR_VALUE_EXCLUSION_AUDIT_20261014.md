# Unit 5 Feedipedia four-value exclusion audit (2026-10-14)

## Scope and reproducibility

Compare the 126-value earlier revision of `data/research/forage_nutrition_research_v5.json` at commit `c7b5c940cbf89038cf34ab8faf6de54430511a30` with the 122-value version on `research/global-plant-evidence-unit5-20261014`. The current `data/research/forage_nutrition_verification_v5.json` reports 122/122 matches against saved copies of Feedipedia pages. This verification does **not** independently validate excluded rows, feeding safety, or underlying analytical samples.

## Four removed values

| Source node | Forage and state | Nutrient | Earlier value | Earlier sample count |
|---|---|---|---|---|
| [12645](https://www.feedipedia.org/node/12645) | *Trifolium subterraneum*, fresh aerial part | magnesium | 1.7 g/kg DM | 6 |
| [12645](https://www.feedipedia.org/node/12645) | *Trifolium subterraneum*, fresh aerial part | sodium | 2.2 g/kg DM | 33 |
| [12646](https://www.feedipedia.org/node/12646) | *Trifolium subterraneum*, hay | dry matter | 90.2% as fed | 6 |
| [12646](https://www.feedipedia.org/node/12646) | *Trifolium subterraneum*, hay | ether extract | 2.2% DM | 5 |

**Important unresolved discrepancy:** The *earlier research transcription* assigns nonzero sample counts (6, 33, 6, 5) to all four removed rows. A prior conversational report claimed that the original Feedipedia pages showed no Nb for these rows, but the present repository's 122-value verification report contains no checks of excluded rows. Therefore the no-Nb explanation is **not independently established by the current verification artifact**, and the removed values must not be described as conclusively invalid or correctly excluded without direct source-row evidence. In particular, do not confuse the earlier transcribed Nb with the source-page Nb.

## Required follow-up before any restoration or definitive explanation

1. Inspect the saved live-page HTML copies for nodes 12645 and 12646; capture the exact four row labels, mean, unit, Nb, any calculation asterisk, and row/table provenance. Preserve a reproducible page hash and row evidence.
2. Extend `scripts/verify_forage_nutrition_v5.py` or add a separate exclusion audit that checks **excluded** values as well as included values and records a per-row reason.
3. If the source actually prints valid sample counts, investigate why the values were removed; do not silently assert missing Nb. If Nb is missing or the row is derived, record the precise source observation and apply the established inclusion policy consistently.
4. Regenerate research summaries and run research-layer QA after any source-data changes. Do not change feeding grades, merge the PR, or deploy based solely on livestock forage composition.

## Status

Audit documentation only. No restoration of the four values, feeding-grade changes, PR merge, or production deployment.
