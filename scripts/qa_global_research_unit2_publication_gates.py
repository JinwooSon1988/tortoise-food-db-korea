#!/usr/bin/env python3
"""Read-only publication gate for the separate Unit 2 research branch.

Run on a checkout containing data/research/*_v2.json (e.g. Unit 2 branch).
Do not import v2 into public verdict data.
"""
import json
from collections import Counter
from pathlib import Path

root = Path(__file__).resolve().parents[1]
path = root / "data/research/tortoise_plant_evidence_v2.json"
if not path.exists():
    raise SystemExit("Unit 2 evidence JSON missing; run on the Unit 2 research branch")
data = json.loads(path.read_text(encoding="utf-8"))
records = data["records"]
errors = []
if len(records) != 357:
    errors.append(f"Unit 2 evidence count changed: {len(records)}")
ids = [r["evidence_id"] for r in records]
if len(ids) != len(set(ids)):
    errors.append("Duplicate Unit 2 evidence IDs")
counts = Counter(r["evidence_directness"] for r in records)
expected = {"primary_study_read": 323, "local_report_recorded_in_primary_study_read": 12, "statement_of_the_source_read": 16, "reported_in_source_primary_not_read": 6}
if counts != expected:
    errors.append(f"Directness breakdown changed: {dict(counts)}")
for r in records:
    if r.get("feeding_grade") is not None:
        errors.append(f"Research-only grade must be null: {r['evidence_id']}")
    if not r.get("tortoise_scientific_name") or not r.get("plant_name_as_printed"):
        errors.append(f"Taxon or plant name missing: {r['evidence_id']}")
    if r.get("applies_to_other_tortoise_species") not in ("not established by this source", None):
        errors.append(f"Unreviewed cross-species applicability: {r['evidence_id']}")
# Prevent secondary citations from being mislabeled as verified original studies.
unread = [r for r in records if r["evidence_directness"] == "reported_in_source_primary_not_read"]
if len(unread) != 6:
    errors.append(f"Unexpected unread-primary count: {len(unread)}")
for r in unread:
    if r.get("verification_status") != "secondary_source_checked_primary_unread":
        errors.append(f"Unread primary mislabeled as verified: {r['evidence_id']}")
    if r.get("evidence_type") != "secondary_citation_of_species_diet":
        errors.append(f"Unread primary mislabeled as direct evidence type: {r['evidence_id']}")
    if r.get("plant_accepted_name") is not None and r.get("plant_name_check") == "spelling_differs_from_backbone_needs_review":
        errors.append(f"Unresolved secondary name prematurely accepted: {r['evidence_id']}")
moll_secondary = next((r for r in records if r["evidence_id"] == "moll_klemens_1996-07"), None)
if moll_secondary is None:
    errors.append("Missing Moll and Klemens secondary citation")
elif "Secondary citation" not in moll_secondary.get("study_method", "") or "Loveridge and Williams (1957)" not in moll_secondary.get("study_method", ""):
    errors.append("Moll and Klemens secondary citation inherited direct observation method")
for key in ("delaossa_2009-20", "delaossa_2009-21", "delaossa_2009-22", "delaossa_2009-23", "delaossa_2009-24"):
    r = next((x for x in records if x["evidence_id"] == key), None)
    if r is None:
        errors.append(f"Missing De la Ossa secondary citation: {key}")
    elif "Secondary background citation" not in r.get("study_method", ""):
        errors.append(f"De la Ossa secondary citation inherited captive trial method: {key}")
# A primary paper can report interviewees' local knowledge without directly
# observing the feeding event. Preserve that distinction for all 12 records.
local_reports = [r for r in records if r["evidence_directness"] == "local_report_recorded_in_primary_study_read"]
if len(local_reports) != 12:
    errors.append(f"Unexpected local-report count: {len(local_reports)}")
for r in local_reports:
    if r.get("evidence_type") != "local_knowledge_report":
        errors.append(f"Interview report mislabeled as direct observation: {r['evidence_id']}")
    if r.get("feeding_grade") is not None:
        errors.append(f"Local knowledge report received feeding grade: {r['evidence_id']}")
    if r.get("tortoise_scientific_name") not in ("Geochelone platynota", "Indotestudo elongata"):
        errors.append(f"Unexpected species in local-report set: {r['evidence_id']}")
# A conservation plan's plant list is a reviewed secondary summary,
# not 16 independent direct feeding experiments.
review_summaries = [r for r in records if r["evidence_directness"] == "statement_of_the_source_read"]
if len(review_summaries) != 16:
    errors.append(f"Unexpected conservation-plan summary count: {len(review_summaries)}")
for r in review_summaries:
    if r.get("evidence_type") != "conservation_plan_secondary_summary":
        errors.append(f"Conservation-plan summary mislabeled as direct study: {r['evidence_id']}")
    if r.get("verification_status") != "verified_review_document":
        errors.append(f"Conservation-plan source type mislabeled: {r['evidence_id']}")
# Explicitly protect the complete provenance taxonomy, not just special cases.
allowed_provenance_types = {
    "primary_study_read": {
        "direct_study_of_this_tortoise_species",
        "primary_fecal_seed_identification",
        "primary_fecal_taxon_detection_without_observed_feeding",
        "primary_fecal_plant_fragment_identification",
        "field_study_compiled_palatable_plant_list",
        "specialist_husbandry_practice",
        "food_given_by_local_people_observed",
    },
    "reported_in_source_primary_not_read": {"secondary_citation_of_species_diet"},
    "local_report_recorded_in_primary_study_read": {"local_knowledge_report"},
    "statement_of_the_source_read": {"conservation_plan_secondary_summary"},
}
for r in records:
    directness = r.get("evidence_directness")
    evidence_type = r.get("evidence_type")
    if evidence_type not in allowed_provenance_types.get(directness, set()):
        errors.append(f"Contradictory provenance/evidence type: {r['evidence_id']} ({directness} / {evidence_type})")
# Fecal seed recovery is evidence of passage through the gut, not
# independent proof that leaves, flowers, or other plant parts were eaten.
fecal_part_labels = {
    "fragments in feces",
    "small pieces in feces",
    "seeds found in feces",
    "fruit (seeds found in dung)",
}
fecal_records = [r for r in records if r.get("plant_part") in fecal_part_labels]
if len(fecal_records) != 158:
    errors.append(f"Unexpected fecal-evidence record count: {len(fecal_records)}")
for r in fecal_records:
    if r.get("feeding_grade") is not None or r.get("safety_verdict") is not None:
        errors.append(f"Fecal observation promoted to feeding/safety verdict: {r['evidence_id']}")
    if r.get("plant_part") not in fecal_part_labels:
        errors.append(f"Fecal evidence part misrepresented: {r['evidence_id']}")
# Unresolved names must not acquire an accepted taxon by inference.
unresolved_name_statuses = {
    "backbone_match_conflicts_with_source_needs_review",
    "homonyms_in_backbone_author_not_given_needs_review",
    "common_name_only_not_resolved",
    "spelling_differs_from_backbone_needs_review",
    "not_resolved_needs_review",
}
unresolved_records = [r for r in records if r.get("plant_name_check") in unresolved_name_statuses]
if len(unresolved_records) != 45:
    errors.append(f"Unexpected unresolved-taxonomy record count: {len(unresolved_records)}")
for r in unresolved_records:
    if r.get("plant_accepted_name") is not None:
        errors.append(f"Unresolved taxon assigned accepted name: {r['evidence_id']}")
# Preserve two intentional taxonomic exceptions: an unresolved genus
# label and a source that lists two names separately despite synonymy.
taxonomic_exceptions = {
    "pillajo_2020-50": ("genus_kept_as_printed_backbone_status_synonym", "Pennisetum sp.", "Pennisetum"),
    "figueroa_2024-07": ("synonym_in_backbone_but_source_lists_both_names_kept_separate", "Euphorbia cyathophora", None),
}
for r in records:
    if r.get("evidence_id") in taxonomic_exceptions:
        expected = taxonomic_exceptions[r["evidence_id"]]
        actual = (r.get("plant_name_check"), r.get("plant_name_as_printed"), r.get("plant_accepted_name"))
        if actual != expected:
            errors.append(f"Taxonomic exception overwritten: {r['evidence_id']}")
# Routine captive foods on p.160 are not treatments in the flower trial.
routine_foods = [r for r in records if r.get("evidence_type") == "specialist_husbandry_practice"]
if len(routine_foods) != 9:
    errors.append(f"Unexpected routine-captive-food count: {len(routine_foods)}")
for r in routine_foods:
    method = r.get("study_method", "")
    if "routine captive feeding practice" not in method or "not individual treatments" not in method:
        errors.append(f"Routine diet conflated with flower trial: {r['evidence_id']}")
# Foods provided by villagers are not 14 independently witnessed ingestion events.
village_provided = [r for r in records if r.get("evidence_type") == "food_given_by_local_people_observed"]
if len(village_provided) != 14:
    errors.append(f"Unexpected village-provided-food count: {len(village_provided)}")
for r in village_provided:
    method = r.get("study_method", "")
    if "foods provided by local people" not in method or "does not independently establish direct observation" not in method:
        errors.append(f"Village-provided food conflated with direct ingestion: {r['evidence_id']}")
# Direct primary analysis of fecal seeds must not imply witnessed feeding.
seed_study_sources = {"pillajo_2020": 90, "figueroa_2024": 62, "ellis_soto_2017": 2}
for source, expected_count in seed_study_sources.items():
    group = [r for r in records if r.get("source_id") == source]
    if len(group) != expected_count:
        errors.append(f"Unexpected seed-study record count for {source}: {len(group)}")
    for r in group:
        if r.get("evidence_type") != "primary_fecal_seed_identification":
            errors.append(f"Fecal seed study conflated with direct feeding observation: {r['evidence_id']}")
# In the mixed-method Round Island study, only taxa with a reported
# feeding-observation count may be described as directly seen eaten.
round_island = [r for r in records if r.get("source_id") == "moorhouse_gann_2022"]
if len(round_island) != 53:
    errors.append(f"Unexpected Round Island evidence count: {len(round_island)}")
dung_only = [r for r in round_island if "feeding observation" not in r.get("quantity_as_reported", "")]
if len(dung_only) != 29:
    errors.append(f"Unexpected Round Island dung-only count: {len(dung_only)}")
for r in dung_only:
    if r.get("observed_consumption") != "detected in dung; no taxon-specific feeding observation reported in this record":
        errors.append(f"Dung-only taxon mislabeled as observed feeding: {r['evidence_id']}")
    if r.get("evidence_type") != "primary_fecal_taxon_detection_without_observed_feeding":
        errors.append(f"Dung-only taxon mislabeled as direct feeding evidence: {r['evidence_id']}")
direct_observation_taxa = [r for r in round_island if "feeding observation" in r.get("quantity_as_reported", "")]
if len(direct_observation_taxa) != 24:
    errors.append(f"Unexpected Round Island direct-observation count: {len(direct_observation_taxa)}")
for r in direct_observation_taxa:
    if r.get("observed_consumption") != "detected in dung and directly observed eaten (taxon-specific feeding observation reported)":
        errors.append(f"Observed feeding taxon lacks specific evidence label: {r['evidence_id']}")
# A rejected GBIF homonym must not leak its Asteraceae family into
# the unresolved Ceratocephalus record.
cerato = next((r for r in records if r.get("evidence_id") == "lagarde_2003_primary-01"), None)
if cerato is None:
    errors.append("Missing Ceratocephalus taxonomy conflict record")
elif (cerato.get("plant_accepted_name") is not None or
      cerato.get("plant_family") is not None or
      cerato.get("plant_name_check") != "backbone_match_conflicts_with_source_needs_review"):
    errors.append("Rejected Ceratocephalus backbone match leaked into accepted taxonomy")
# Fecal plant fragments are distinct from two observed-foraging records.
for n in range(1, 7):
    evidence_id = f"moll_klemens_1996-{n:02d}"
    item = next((r for r in records if r.get("evidence_id") == evidence_id), None)
    expected = "primary_fecal_plant_fragment_identification" if n <= 4 else "direct_study_of_this_tortoise_species"
    if item is None or item.get("evidence_type") != expected:
        errors.append(f"Incorrect Moll-Klemens evidence modality: {evidence_id}")
# Bayley-Highfield's Table 1 compiles mixed observation/report sources;
# no row may be promoted to an individually witnessed feeding event.
morocco_list = [r for r in records if r.get("source_id") == "bayley_highfield_1996"]
if len(morocco_list) != 24:
    errors.append(f"Unexpected Moroccan compiled plant-list count: {len(morocco_list)}")
for r in morocco_list:
    if r.get("evidence_type") != "field_study_compiled_palatable_plant_list":
        errors.append(f"Compiled palatability list mislabeled as direct feeding: {r['evidence_id']}")
by_id = {r["evidence_id"]: r for r in records}
for key in ("lagarde_2003_primary-01", "lagarde_2003_primary-02"):
    if key not in by_id:
        errors.append(f"Critical source review missing: {key}")
if "lagarde_2003_primary-01" in by_id:
    r = by_id["lagarde_2003_primary-01"]
    if r.get("plant_accepted_name") is not None or "conflict" not in str(r.get("plant_name_check", "")):
        errors.append("Ceratocephalus taxonomy conflict must remain unresolved")
if "lagarde_2003_primary-02" in by_id:
    r = by_id["lagarde_2003_primary-02"]
    if r.get("plant_part") != "flower" and r.get("plant_part") != "flowers":
        errors.append("Papaver pavoninum flower-specific evidence was lost")
if errors:
    raise SystemExit("\n".join(errors))
print(f"Unit 2 research-only publication gates passed: {len(records)} evidence records, no feeding grades")
