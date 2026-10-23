# Batch 004 (automatic extraction, reviewed passage by passage)

Pipeline (`scripts/evidence_corpus/batch_004/`, every request through `scripts/polite_http.py`):

1. `make_docs.py` - every full text saved by batches 001-003 (Europe PMC JATS XML, batch 002-003 PDF text), once each.
2. `discover.py` - Europe PMC open-access subset: land tortoises x diet / faeces / herbivory / captivity / nutrition /
   toxicity (title-abstract), and tortoise genera x diet wording anywhere in the full text. `www.ebi.ac.uk` asks for
   `Crawl-delay: 10`, so downloads run one per 10 s; new documents are ranked and capped per run.
   `discover_openalex.py` (open-access PDFs outside PMC) stopped at the first request: OpenAlex answered HTTP 429
   (quota), and the client does not retry around a quota.
3. `extract.py` - candidates: a plant binomial and a feeding word in the same sentence or JATS table row, the name
   within 12 words of the feeding word or the tortoise; negations, toxicity wording, other animals or people,
   availability comparisons and nutrient-content tables go to review; PDF table lines and run-together PDF text are
   skipped; abbreviated genera are expanded only to a binomial written in full in the same document.
4. `normalize.py` - GBIF Backbone: genus check, strict species match (exact, recorded synonym or spelling variant),
   isolation of names that cannot be linked (no match, higher rank, fuzzy, doubtful, several matches, not a plant).
5. `assemble.py` - quote re-found in the saved text, P1-held claims excluded, duplicates of batches 001-003 removed,
   one record per plant x tortoise x source x type, and only records with an `accept` in `review_decisions.jsonl`.
6. `audit_sample.py` - prints each candidate with the context of its quoted passage for the review.

Files here: `review_decisions.jsonl` (accept / reject with the reason, for every linked or rejected record),
`records_with_quotes.jsonl.gz` (the quoted passage of every linked record, <= 25 words), `undecided.jsonl`
(candidates not reviewed yet). Records are labelled `full_text_auto_extracted`: found automatically and re-found
verbatim; the review was done by Claude reading the passage in context, which is not a person reading the source,
so they are never counted as "checked in the original" and give the research status `evidence_auto_extracted`.

## Run of 2026-10-23

| Step | Count |
|---|---|
| Documents processed | 4,261 (3,813 + 189 Europe PMC JATS, 259 PDF texts); 3,648 not about tortoises, 115 keeper/community skipped |
| Documents with candidates | 176 |
| GBIF requests | 2,284, 0 failed (genus check 1,845; species match 263; species record 88; vernacular names 88) |
| Europe PMC requests | 233: 203 ok, 24 retried after HTTP 500, 6 failed (2.6 %); 189 of 436 ranked new documents fetched before the run was stopped (no tortoise diet content in the new ones) |
| OpenAlex | stopped at the first request (HTTP 429 quota) |
| Candidate records after the strict rules | 1,408 (1,853 more sent to review by the rules); names linkable in GBIF 129 |
| Removed as duplicates of batches 001-003 | 157 (+6 within the batch) |
| Reviewed | 35: 26 accepted, 9 rejected (reasons in review_decisions.jsonl) |
| Linked | 26 records, 16 sources; 17 catalog species get a record, 5 of them had no evidence before; 9 records are for plants in the reviewed list of 182 and are not shown in the catalog |

Two earlier rule sets were audited and replaced: 50 + 60 random candidates read, precision about 78 % and 65 %
(other animals' diets, people, two-column PDF text, nutrient tables, negations, wrong genus expansion).

Resume: every step keeps a JSONL checkpoint next to its output; rerunning a step skips finished work and retries
transient failures only.
