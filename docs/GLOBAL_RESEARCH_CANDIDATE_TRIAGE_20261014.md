# Global research candidate triage — 2026-10-14

Scope: Claude's research-only `data/research/plant_candidates_v1.json` in PR #304. This is an inventory and editorial triage, **not** a publication approval or feeding-grade assignment.

## Inventory verified against the research JSON

| Current database relationship | Count | Editorial next action |
|---|---:|---|
| `not_in_database` | 129 | Verify exact taxonomy, evidence source, plant part and species applicability before any public addition |
| `species_already_in_database` | 17 | Compare evidence with existing public entry; preserve existing grade pending separate review |
| `genus_level_record_in_database` | 25 | Do not merge species-specific evidence into genus-level feeding conclusions |
| `unresolved_name_not_a_candidate` | 28 | Resolve printed taxon/name first; no automatic entry |
| **Total** | **199** | **Research only** |

The 129 entries marked `not_in_database` are **candidate records**, not 129 approved foods. Some are genus-level and require additional identification. The seven `negative_record_only` candidates represent reported avoidance/rejection and must not be converted to a blanket toxicity or safety verdict.

## Minimum review fields before publication

1. Original source, page and directness: distinguish primary full text from secondary citation and abstract-only evidence.
2. Scientific identification: accepted name, synonym, genus-only or unresolved printed name; do not silently conflate taxa.
3. Tortoise taxon: identify the observed species and mark extrapolation to other species as unestablished.
4. Observation: consumption, avoidance or captive feeding is not itself a feeding-safety trial.
5. Plant part and preparation: leaf, flower, stem, seed, fresh/dried; retain `not stated` where applicable.
6. Known toxicity or antinutritional concerns: separately verify with appropriate veterinary/botanical evidence; no inference from avoidance alone.
7. Nutritional data: verify the measured taxon, plant part and as-fed versus dry-matter basis; livestock forage values do not automatically support a tortoise verdict.
8. Korean/English descriptions, accurate image identification and source links.
9. Independent approval for any change to the public A/B/C/D feeding grade.

## Release policy

Do not automatically publish these records, change `data/plants.json`, generate public plant pages or merge PRs from this triage. Prioritize the 17 existing species records for **evidence enrichment without grade changes** after direct source review; review the 129 new candidates individually; hold the 28 unresolved names. This prioritization is a workflow recommendation, not a conclusion that the 17 records are already scientifically validated.
