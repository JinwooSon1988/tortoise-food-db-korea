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


## Approved backbone sources (reviewed 2026-09-19)

The machine-readable registry is `docs/GLOBAL_PLANT_SOURCE_REGISTRY.json`.

Initial hierarchy:
1. Kew WCVP — primary global vascular-plant name/synonym reconciliation backbone.
2. World Flora Online — independent global cross-check and taxonomic-expert-network signal.
3. Catalogue of Life Base Release — independent cross-check/source graph; prefer Base over Extended where scrutiny is the priority.
4. Korean/regional authoritative checklists — occurrence, Korean accepted names and regional annotations after dataset-level review.

Cross-source disagreement is stored as a conflict for review, not silently resolved by source priority.
