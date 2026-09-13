# 데이터 모델

plant_master
- id
- Korean common name
- English common name
- scientific name
- family
- aliases
- identity status
- market availability

nutrition_record
- plant_id
- source provider / source record id
- values per 100 g edible portion
- derived Ca:P
- review status

evidence_record
- evidence type
- taxonomic scope
- directness
- citation / DOI
- what it supports
- what it does NOT support

species_profile
- taxon
- ecological feeding group
- life stage

suitability_assessment
- plant_id × species_id × life_stage
- grade A/B/C/U
- role in mixed diet
- limitations
- evidence ids
- last reviewed at
