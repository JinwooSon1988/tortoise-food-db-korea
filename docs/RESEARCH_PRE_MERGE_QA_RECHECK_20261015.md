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

### 4. The gap register left out 13 live records whose citation is open

`research_gap_register_v6.json` listed only unit-1 records still marked `secondary_citation_primary_not_read` (74 in 16 groups).
Not listed were 87 − 74 = 13 live records whose evidence still rests on an unread or non-supporting original:

* 5 × `crm096_elongata_2016` — Sriprateep et al. 2013 was read and does not name the plant; van Dijk 1998 and Ihlow pers. obs. are unread;
* 5 × `delaossa_2009-20..24` (cited as Moskovits 1981; see the unit-2 Moskovits citation audit) and `moll_klemens_1996-07`
  (Loveridge and Williams 1957) — unit-2 secondary citations;
* 2 × `crm109_agassizii_2019-05/06` — Prose and Wilshire 2000 was read in unit 3 and does not support the statement
  (the report never mentions tortoises). Now on hold (section 5).

The register now has `other_citations_not_read` (3 groups, 11 records) and `unit_1_citations_read_not_supporting` (2 records);
the existing section and its totals are unchanged. The 21 unread-primary records not listed are confirmed in their primary and superseded.
Unresolved scientific names: 48, unchanged; the 130 index records without an accepted name and outside the register are all
`common_name_only` ("dry grass" etc.), not unresolved scientific names.

### 5. crm109: the cited source does not support the statement — on hold

Berry and Murphy (2019, CRM 5.109, *Gopherus agassizii*) write that the cover "of some annual forbs consumed by tortoises, e.g., desert
dandelion (*Malacothrix glabrata*) and Fremont's pincushion (*Chaenactis fremontii*) was lower in tank tracks (Prose and Wilshire 2000)".
The citation belongs to the tank-track cover finding; the clause "consumed by tortoises" has no citation of its own.
Prose and Wilshire 2000 (USGS Open-File Report 00-512) was read in unit 3 and read again for this check
(https://pubs.usgs.gov/of/2000/0512/pdf/of00-512.pdf, fetched 2026-10-15, SHA-256 5407fec988dbea96…, 11,616 words in the text layer):
"tortoise" does not occur, *Malacothrix* does not occur, and *Chaenactis fremontii* occurs only as an annual whose cover fell in tank tracks.

`crm109_agassizii_2019-05` and `-06` are therefore on hold in `evidence_index_v4/v5` (`build_global_plant_evidence_research_v4.py`
holds every unit-1 record whose ledger status is `cited_source_read_does_not_support_the_statement`). `review_queue_v4.records_on_hold`
lists them with the cited publication, the source id that was read, and the ledger's finding. They no longer count in tiers, detection
methods or per-tortoise totals; the records and the account's wording stay in the database. The two plants keep their independent
primary records (Oftedal 2002, `oftedal_2002-04` and `-07`), so the candidates now show only those as live evidence.

### 6. Verification queue for the unread originals

`data/research/primary_verification_queue_v6.json` (`scripts/build_primary_verification_queue_v6.py`) lists the 19 cited publications
whose original has not been read, with the 85 live records that rest on them: 16 unit-1 citations (74 records) and 3 other citations
(11 records: Moskovits 1981, van Dijk 1998 with Sriprateep et al. 2013 and a personal observation, Loveridge and Williams 1957).
The earlier "87" counted the two crm109 records as well; their original was read, so they are on hold rather than queued.
Each entry gives the search status, the next step and the records with no independent primary record (81 of 85), which sets the order.
Every entry is `awaiting_original`. A record leaves the queue only when its original is read in a unit build; reading it never raises
the account's record, and an observation found in the original becomes a new record from that original.

### New guards (`qa_global_plant_evidence_research_v7.py`)

* tiers 1, 2 and 2b must agree with `wild_or_captive` in both evidence indexes;
* a candidate's best tier cannot be a wild feeding study unless one of its records is;
* every reviewed unit-2 correction must be present in the evidence file;
* the v2 summary's nutrition value counts must equal the nutrition files;
* every live record whose original is unread or non-supporting is listed in the gap register;
* a record whose cited source was read and does not support it is on hold;
* the verification queue holds exactly the register's unread citations, every entry is `awaiting_original`, and every queued record is
  still a live tier-8 secondary citation (none raised or held without a read original).

They fail on the data before this change (3 and 13 errors) and pass after it; the hold and queue guards were checked the same way.

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
