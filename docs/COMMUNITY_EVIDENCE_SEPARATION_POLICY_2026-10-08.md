# Community observation evidence separation — 2026-10-08

## Purpose
Capture useful husbandry leads worldwide without laundering anecdote into feeding safety evidence. This is an internal editorial and data acceptance policy, **not** a claim that listed sources have been independently verified.

## Data lanes
1. **Published feeding assessment:** existing source-linked scientific/veterinary assessment, with explicit species and evidence distance. Community reports never alter A–D grades or numeric nutrients.
2. **Research lead:** a URL or citation awaiting source-level review. No endorsement, safety inference or publication.
3. **Unverified keeper observation:** a documented firsthand report, separated from a secondhand recommendation, with uncertainty and counterexamples.
4. **Verified research follow-up:** independently retrieved primary study or official composition record, evaluated under the existing nutrition/evidence gates. Original community lead remains attributed but does not itself become a study.

## Minimum schema for an observation candidate
- `source_url`, `platform`, `observed_or_posted_at` (nullable), `retrieved_at`
- `observation_type`: firsthand / secondhand / advice_only / unknown
- `animal_taxon_original`, `animal_taxon_normalized` (nullable)
- `plant_name_original`, `plant_taxon_normalized` (nullable), `plant_part` (nullable), `preparation_state` (nullable)
- `reported_exposure` and `reported_outcome` as short paraphrases, clearly attributed; unknown when absent
- `duration`, `number_of_animals`, `husbandry_context` (nullable)
- `limitations`: self-report, no control, no diagnostic confirmation, confounding husbandry conditions, uncertain identity, or unknown duration as applicable
- `contradictory_reports` (source-linked list) and `independent_validation`: unverified / partial / independently_supported / contradicted
- `copyright_access_status`, `editorial_status`: lead / reviewed / excluded / eligible_for_reference

## Publication rules
- Do not show a keeper's claim on a verdict card or above the primary feeding safety explanation.
- If displayed, label **“사육자 경험 · 학술적으로 검증되지 않음”**, provide an accessible original source link and date when known, and keep in a separately expandable section.
- Do not publish precise user handles, profile details, images, full post text, or identifiable personal information unless necessary and permitted. Use short attributed paraphrases; respect copyright, terms, robots and API limits.
- Never state “safe,” “recommended,” or dose/frequency solely because a forum reports successful feeding. Absence of reported harm is not proof of safety.
- Conflicting accounts and negative observations must not be suppressed. Do not present counts of forum posts as incidence, prevalence, controlled trials or consensus.
- No automated publication from scraping. Require human review of relevance, taxon, plant part, provenance and potential harm.

## Editorial gate
`candidate -> source_access_checked -> identity_reviewed -> evidence_distance_reviewed -> privacy_copyright_reviewed -> editorial_reviewed -> eligible_for_reference`

Any failed gate remains internal. If a source is removed, access-restricted, or cannot be cited reliably, keep a private audit record without reproducing its content publicly.

## Example (illustrative, not an actual observation)
A keeper says a tortoise ate a leaf for several months without an obvious problem. The report supports only that the keeper described an exposure and outcome; it cannot establish chronic safety, species-wide applicability or nutritional adequacy.

## Existing seed
See `data/global_source_discovery_seed_2026_10_08.json`. Its six URLs are discovery leads, not six accepted observation records. Future Claude intake should respect this separation and the global nutrition protocol.
