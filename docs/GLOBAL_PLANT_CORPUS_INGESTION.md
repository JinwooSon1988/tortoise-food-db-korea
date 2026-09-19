# Global Plant Corpus ingestion contract

This corpus is an identity/search backbone, not a feeding verdict list.

## Canonical taxonomy
Prefer an authoritative global vascular-plant backbone and preserve source identifiers and observed dates. Kew WCVP/POWO is suitable as a primary reconciliation backbone; regional authoritative lists can override or annotate regional occurrence when documented.

## Separation rules
- Availability is metadata, never feeding safety.
- identity_only records cannot contain a feed assessment.
- Synonyms remain explicit records/relationships; never silently collapse them.
- Unknown feeding evidence stays unknown.
- Taxonomic acceptance and feeding suitability are separate evidence domains.
- Raw candidates must be staged and reconciled before promotion to this corpus.

## Pipeline
raw candidate -> normalize -> reconcile accepted name/synonym -> provenance -> geography/common names -> feeding evidence discovery -> toxicology/nutrition evidence -> conflict checks -> human-reviewed assessment -> public evidence state

## Scale
The architecture must support a global vascular-plant corpus while the existing curated plant assessments remain source truth for public feeding verdicts.
