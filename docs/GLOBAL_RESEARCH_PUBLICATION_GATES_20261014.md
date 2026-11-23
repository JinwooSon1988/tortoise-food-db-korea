# Global research evidence: publication gates (2026-10-14)

Scope: independent review of PR #304's research-layer documentation and record schema. This document does not approve a plant for feeding and does not change the public database.

## Observed baseline

- 169 species-linked evidence records, of which 46 were read directly in primary papers; other entries may cite primary studies through peer-reviewed species accounts.
- 129 new candidate plants (95 species-rank, 34 genus-rank). Candidate status is not a feeding verdict.
- 7 avoidance/negative records and records naming plants with potential toxicity are retained.
- 11 forage-nutrition records originate in livestock-oriented composition tables; their presence does not establish tortoise safety.
- Missing or limited species coverage includes Aldabra, Galápagos, yellow-foot and red-foot tortoises.
- The research JSON explicitly declares `research_only_not_published` and carries null feeding grades.

## Mandatory gates before public integration

1. **Identity**: accepted botanical name, synonym history, taxonomic rank, and exact match to the existing plant record. Genus-only and family-only names must not be silently promoted to a species.
2. **Species applicability**: identify the tortoise taxon studied and whether the observation was wild or captive. No cross-species extrapolation without an explicit rationale and qualification.
3. **Plant part and preparation**: distinguish leaf, stem, flower, fruit, seed, hay, fresh forage and unspecified parts. Never attach nutrition values to a different part or moisture basis without a conspicuous warning.
4. **Evidence directness**: preserve the distinction between directly read primary research, peer-reviewed accounts quoting primary literature, abstracts, and unverified reproductions. Display the original source and limitations.
5. **Safety**: wild consumption, inclusion in a commercial seed mixture, or livestock forage composition must never by itself justify an A/B/C feeding grade. Negative records and potential toxicity require explicit review.
6. **Verdict approval**: propose any grade change separately with species scope, benefits, hazards, evidence and reviewer sign-off. Keep the existing public verdict until approved.
7. **User-facing parity**: Korean and English must communicate the same caveats, species limitations and nutrition evidence states, with readable mobile layouts.
8. **Visual verification**: photograph must identify the correct botanical species and edible plant part, with traceable license and attribution.
9. **Regression**: validate canonical plant IDs, source IDs, generated KO/EN pages, internal links and CI before merging; separately inspect the deployed pages after an approved deployment.

## Priority review queue

1. Directly verify the 102 species-account records that cite unread primary studies; retain indirect status until the original is checked.
2. Resolve held original sources and the four held Russian tortoise records; do not present them as confirmed.
3. Expand primary-source coverage for Aldabra, Galápagos, yellow-foot and red-foot tortoises.
4. Review hazardous or potentially toxic plants (including *Drimia maritima*, *Tamus communis*, *Arum*, *Ranunculus*, *Digitalis*) before any user-facing feeding recommendation.
5. Check genus-only names, unresolved spellings, and ambiguous seed-mixture ingredients.
6. Match forage nutrition by accepted taxon, sampled part, preparation, measurement basis and source date.

## Release decision

**Not ready for automatic publication.** The existing QA proves structural consistency of the research layer, not feeding safety, primary-source verification, image accuracy or public-page correctness. No candidate should inherit a positive grade simply by appearing in the research corpus.

## Explicit negative-record review queue (source-data audit)

The seven records marked `is_negative_record=true` in PR #304 are listed below. These are **reported avoidance/rejection observations**, not proof that each plant is toxic, and not general feeding prohibitions for every tortoise.

| Evidence ID | Tortoise | Plant as printed | Reported observation | Source status |
|---|---|---|---|---|
| `crm122_marginata_2023-18` | *Testudo marginata* | *Thymus capitatus* | usually avoided | peer-reviewed account |
| `crm059_hermanni_2011-09` | *Testudo hermanni* | *Thymus* | generally rejected | peer-reviewed account |
| `crm059_hermanni_2011-10` | *Testudo hermanni* | *Lavandula* | generally rejected | peer-reviewed account |
| `crm059_hermanni_2011-11` | *Testudo hermanni* | *Rosmarinus* | generally rejected | peer-reviewed account |
| `crm059_hermanni_2011-12` | *Testudo hermanni* | *Euphorbia* | generally rejected | peer-reviewed account |
| `crm059_hermanni_2011-13` | *Testudo hermanni* | *Inula viscosa* | generally rejected | peer-reviewed account |
| `lagarde_2003-04` | *Testudo horsfieldii* | grasses (unidentified) | avoided | original not read; held |

**Integration rule:** retain the original observed behavior, tortoise species, printed plant name and source status; do not translate `avoided` into `toxic`, or `consumed` into `safe`. The unidentified-grass record cannot be mapped to a named grass species. The candidate records for all seven observations are marked `negative_record_only=true`, including synonym/printed-name variants.

