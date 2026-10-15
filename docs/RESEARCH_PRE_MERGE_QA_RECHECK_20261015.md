# Research layer pre-merge QA recheck — 2026-10-15

Scope: PR #313 (`research/pre-merge-integration-qa-20261014`) and the stack it closes (#304, #306–#312), re-checked after a restart.
Only research files (`data/research/`) and research scripts change. No feeding grade, public plant data, UI, SEO or translation file is touched.

## Findings and fixes

### 1. Lambert 1993 kept the wild tier after it was narrowed

`lambert_1993-01` (*Centrochelys sulcata* on *Eleusine indica*) was reclassified in unit 2 (c28d984f) as a single feeding observation of a
previously captive female allowed to roam near farmland. `wild_or_captive` and `evidence_class` were changed, but `tier_of()` in
`build_global_plant_evidence_research_v3.py` had no branch for the new class `field_observation_of_previously_captive_tortoise`.
The record therefore fell through to `1_wild_feeding_study_read` ("야생 섭식 연구(원문 열람)") in `evidence_index_v4/v5`, and the
*Eleusine indica* candidate in `plant_candidates_v3/v4` showed a wild feeding study as its best evidence.

Neither existing tier fits: tier 2 is a study inside an enclosure of natural vegetation and tier 3 is a captive feeding trial.
A tier `2b_previously_captive_animal_field_observation_read` ("과거 사육 개체의 야외 섭식 관찰(원문 열람)") is added; it sorts after
tier 2 and before tier 3. The two QA copies of `tier_of` (units 3 and 4) carry the same branch. Lambert still does not count as an
independent wild observation or as a captive feeding record.

### 2. A full rebuild reverted the unit-2 corrections

The 379 field corrections to 282 unit-2 records (commits 661ede05..82b383e5: unread primaries, conservation-plan summaries,
faecal-seed and dung-only records, compiled palatability lists, Lambert, Ceratocephalus family, two Moorhouse-Gann quantities)
were made in the generated `tortoise_plant_evidence_v2.json` only. Running the unit-2 builder restored the uncorrected records;
QA caught it (unit-2 gates, unit-2 QA, integration QA failed), but the committed data could not be reproduced.

The corrections now live in `data/research/record_corrections_v2_editorial.json`, one row per field with the value the builder
produces, the reviewed value, and the commit that made it (traced commit by commit from the git history). The unit-2 build applies
a row only while the built value still equals the recorded one; if the transcription changes, the build stops for review.

### 3. Downstream values that the corrections had not reached

* `research_layer_summary_v2` said unit 1 keeps 113 nutrition values; `forage_nutrition_research_v1.json` keeps 115 since the
  Feedipedia row-reader rebuild (246282a1).
* `plant_candidates_v2` still gave the unresolved "Ceratocephalus falcatus" the rejected GBIF homonym family Asteraceae
  (removed from the evidence record in 92114f34; *Ceratocephala* is Ranunculaceae in units 3 and 4).
* Tier counts in `research_layer_summary_v3/v4` (one record moves from tier 1 to tier 2b).

### New guards (`qa_global_plant_evidence_research_v7.py`)

* tiers 1, 2 and 2b must agree with `wild_or_captive` in both evidence indexes;
* a candidate's best tier cannot be a wild feeding study unless one of its records is;
* every reviewed unit-2 correction must be present in the evidence file;
* the v2 summary's nutrition value counts must equal the nutrition files.

They fail on the data before this change (3 errors) and pass after it.

## Rechecks with no change needed

* Feedipedia 11865: dry matter, ether extract, ash and calcium have a blank Nb on the page and stay excluded; 165 and 72 are kept
  only on crude protein and phosphorus, where the page prints them. The six tannin values and the two 11865 values added by the
  row reader were compared again with the live pages (11650, 11723, 11865, 12063, 19703, fetched 2026-10-15): mean and Nb match.
  This satisfies the requirements in `FEEDIPEDIA_11865_SOURCE_ROW_AUDIT_20261014.md`; the 113-entry count in
  `UNIT2_FEEDIPEDIA_SAMPLE_COUNT_COVERAGE_AUDIT_20261014.md` describes the file before that rebuild (now 119 kept, 4 excluded).
* No excluded nutrient value is kept again; no research record carries a feeding grade.

## Reproducibility

Units 1–5 and the Feedipedia audit rebuilt offline from the GBIF, WFO and Feedipedia caches: the output equals the committed files,
and a second rebuild changes nothing.
