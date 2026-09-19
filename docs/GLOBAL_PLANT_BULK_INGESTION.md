# Global plant bulk-ingestion pipeline

Worldwide collection is intentionally permissive at the candidate stage and strict at promotion.

1. Acquire records from authoritative global/regional taxonomic datasets under their applicable terms.
2. Preserve source identifiers, URLs, observed date and license metadata.
3. Run `scripts/stage_global_plant_candidates.py`.
4. Staging remains `identity_only`; feeding verdict fields are forbidden.
5. Reconcile accepted names, synonyms and ambiguous names against the chosen taxonomic backbone plus regional authorities.
6. Promote only reconciled records into `data/global_plant_corpus.json`.
7. Discover feeding/toxicology/nutrition evidence separately.
8. A reviewed assessment may be created only after evidence review.

The pipeline therefore allows very broad worldwide collection without allowing collection volume to manufacture feeding certainty.
