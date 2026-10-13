# Global evidence acquisition protocol — 2026-10-14

## Scope
No country, language, biome or institution restriction. Search worldwide for tortoise forage, grasses, hays, weeds, wildflowers, browse and plant nutrition. Include African, South Asian, East Asian, Central Asian, Middle Eastern, European, American and Oceanian research, local-language sources, universities, governments, botanical institutions, zoos, veterinary publications and keeper communities. Do not treat English-language search results as exhaustive.

## Collection fields (internal only)
plant_id; accepted_scientific_name; synonym_used_in_source; plant_part; preparation; locality; original_language; source_title; source_url_or_doi; author_or_institution; publication_year; source_type; species_observed; measurement_or_claim; units_and_basis; method; directness; limitations; reviewed_at; verification_status; licensing_notes.

## Evidence distinctions
- Direct laboratory nutrient value: display measured value only with matching taxon, part, units, fresh/dry basis and source.
- Related nutrient value: show with explicit taxon/part/preparation mismatch; never substitute as direct measurement.
- Qualitative nutrition statement: summarize the claim and cite it; do not invent numerical values.
- Wild dietary observation: proves an observed consumption event, not captive safety or suitability.
- Keeper-community report: anecdotal practice only; not proof of safety, long-term tolerance or optimal feeding.
- Toxicology/veterinary contraindication: preserve original scope and species, do not erase conflicting findings.
- No linked source: absence in this database only, never assert global absence.

## UI contract
Keep existing three nutrition filter states unchanged: 검증된 영양자료 / 참고자료만 있음 / 연결 자료 없음. Enrich content inside existing detail layout; do not introduce extra filter categories. Show the actual reference material when available rather than displaying the same empty-state copy as '연결 자료 없음'.

## QA gates
Validate source existence, botanical identity, edible part, original claim, numerical units, translations and image license. Flag ambiguity for review. Never turn anecdote into a feeding verdict or silently fill missing numbers with zero. Never merge a PR with failing CI or claim deployment without live verification.

## Search approach
For each candidate, search accepted Latin binomial and synonyms together with vernacular names in source languages; search ecology/diet, forage analyses, anti-nutrients and toxicology separately. Maintain explicit coverage gaps and avoid duplicating the same dataset republished across websites. Use original publications when possible.


## Prepared plant forms and outdoor sowing intake (2026-10-14 extension)
Capture fresh, hay, air-dried, oven-dried, leaf meal, flower meal and mixed cut forage separately. Store the exact processing method, harvested plant part, moisture basis (as-fed versus dry matter), laboratory method and source. Do not infer nutrient changes from comparing unrelated fresh and hay samples.

For outdoor enclosure seed mixes, preserve the full label ingredient list, Latin names where verified, seed proportions where disclosed, country, seed treatment/pesticide status and invasive-plant concerns. Commercial mixes and keeper sowing diaries establish what is marketed or cultivated, not safety or suitability for tortoises.

Do not prioritize grasses to the exclusion of flowers, weeds, succulents, browse, trees or regionally native plants. Source coverage must include non-English institutions and primary research worldwide.

Existing reference nutrition already includes timothy fresh and hay records; reconcile against those before adding anything. Keep the existing three nutrition filter labels unchanged and enrich only the underlying records and detail content. Never assign a feeding grade from nutrient chemistry or anecdotal use alone.
