# Unit 2 spelling review — source verification audit (2026-10-14)

## Scope and method

Cross-checked all 13 spelling-discrepancy IDs against `data/research/tortoise_plant_evidence_v2.json` on the Unit 2 research branch. This is an **internal source-transcription audit**, not an independent re-reading of the papers and not a botanical authority determination. The external De la Ossa (2009) PDF endpoint was attempted but could not be accessed in this session; no claims about its original printed spellings are made.

## Evidence directness and exact part

| Evidence ID | Transcribed name | Page/table recorded | Directness in dataset | Part recorded |
|---|---|---|---|---|
| bayley_highfield_1996-06 | Launaea residifolia | 41 | primary_study_read | not stated |
| bayley_highfield_1996-08 | Linaria incarta | 41 | primary_study_read | not stated |
| bayley_highfield_1996-16 | Cucumis sativu | 41 | primary_study_read | not stated |
| bayley_highfield_1996-19 | Lycopersicon lycopersicon | 41 | primary_study_read | fruit |
| bayley_highfield_1996-23 | Solanum tuberocum | 41 | primary_study_read | leaves |
| pillajo_2020-13 | Tournefortia rufo-sericea | 55 | primary_study_read | seeds found in feces |
| figueroa_2024-02 | Casuarina equesitifolia | Table 2 | primary_study_read | seeds found in feces |
| figueroa_2024-32 | Physalis walterii | Table 2 | primary_study_read | seeds found in feces |
| figueroa_2024-46 | Eustachys petrea | Table 2 | primary_study_read | seeds found in feces |
| delaossa_2009-20 | Duquetia surinamensis | 158 | **reported_in_source_primary_not_read** | not stated |
| delaossa_2009-24 | Bagassa guianenesis | 158 | **reported_in_source_primary_not_read** | not stated |
| dlugosz_2015-04 | Plantago maior | 3-4 | primary_study_read | whole above-ground parts |
| sriprateep_2013-13 | Morinda citriforia | 28-29 | primary_study_read | not stated |

## Findings and required corrections to interpretation

1. **11/13** records are labeled `primary_study_read` by the research dataset. This status is inherited metadata, not independent verification performed in this audit.
2. **2/13** records, `delaossa_2009-20` and `delaossa_2009-24`, are explicitly **not primary-read**. Their names cannot be presented as independently verified original spellings. Prior spelling-hypothesis notes should be read with this limitation.
3. **4/13** records report **seeds in feces**, not direct observation of leaves being eaten: `pillajo_2020-13`, `figueroa_2024-02`, `figueroa_2024-32`, `figueroa_2024-46`.
4. `bayley_highfield_1996-19` is **fruit**, while `bayley_highfield_1996-23` is **leaves**. Neither supports extrapolating safety to other plant parts.
5. **No accepted botanical names were assigned** in the underlying evidence records. Editorial suggestions in `GLOBAL_RESEARCH_UNIT2_SPELLING_REVIEW_20261014.md` remain unverified hypotheses.

## Next source-first action

Retrieve the original De la Ossa (2009) study through an accessible publisher or archive copy; compare page 158 and any referenced source studies, then record exact quoted spellings, botanical authors, page/table and evidence provenance. For the other 11, independently inspect the specified original page/table and cross-check botanical authorities. Until then, retain source spellings, unresolved status and null feeding grades.
