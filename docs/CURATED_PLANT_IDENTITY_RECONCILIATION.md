# Curated plant identity reconciliation policy

## Classification

Every curated food identity must resolve to exactly one review state:

- `exact_accepted` — exact name maps to one accepted backbone taxon.
- `synonym_review` — supplied name is treated as a synonym by the backbone; accepted-name migration requires review.
- `infraspecific_review` — cultivar/variety/subspecies treatment needs reconciliation across botanical and horticultural usage.
- `genus_scope` — the food record intentionally represents multiple species (for example `Taraxacum spp.`); never collapse automatically.
- `hybrid_review` — hybrid identity requires explicit parent/hybrid treatment review.
- `unresolved` — no defensible reconciliation yet.

## Non-negotiable separation

Taxonomic reconciliation changes identity metadata only. It never creates, upgrades, downgrades, or deletes a feeding verdict.

A public common-name food record may remain stable while its canonical taxonomic relationship is revised. Historical names are retained as searchable synonyms where licensing/provenance permits.

## Infraspecific and market-food rule

Market foods frequently use horticultural names that do not map one-to-one onto a modern global taxonomic backbone. Therefore strings containing `var.`, `subsp.`, cultivar concepts, market groups, or food-form labels are not silently rewritten merely because a backbone prefers a broader species concept.

Review must record:
1. submitted/market name;
2. backbone treatment;
3. accepted taxon if applicable;
4. regional or horticultural treatment where material;
5. plant part / food form;
6. whether the identity difference can change interpretation of feeding evidence.

## Genus-scope rule

`spp.` records are search/food concepts, not assertions that all species in the genus have identical feeding suitability. Species-level evidence remains species-level unless a reviewed assessment explicitly supports broader transfer.

## Conflict rule

When WCVP, WFO, Catalogue of Life, or a regional authority disagree, preserve the disagreement and provenance. Do not resolve by numeric voting and do not allow search convenience to masquerade as taxonomic certainty.
