#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "ibera_direct_feeding_evidence_v56.json"

obj = json.loads(DATA.read_text(encoding="utf-8"))
assert obj["version"] == "5.6"
assert obj["feeding_verdict_use"] is False
rules = obj["rules"]
for key in [
    "wild_occurrence_is_not_captive_percentage",
    "observed_consumption_is_not_unlimited_safety",
    "genus_observation_is_not_exact_species_evidence",
    "plant_part_scope_must_be_preserved",
    "regional_population_scope_must_be_preserved",
]:
    assert rules.get(key) is True, key

sources = {s["source_id"]: s for s in obj["sources"]}
assert set(sources) == {"iftime_ibera_dobrogea_2012", "mitrevichin_ibera_bulgaria_2023"}
for sid, src in sources.items():
    assert src["taxon"] == "Testudo graeca ibera", sid
    assert src.get("supports"), sid
    assert src.get("does_not_support"), sid

observations = obj["observations"]
assert observations
for row in observations:
    assert row["source_id"] in sources
    assert row["directness"] == "exact_subspecies_wild_observation"
    assert row["identity_scope"]
    assert row["source_plant"]

# Exact-species evidence is intentionally narrow.
chicory = [r for r in observations if r.get("plant_id") == "chicory"]
assert len(chicory) == 1
assert chicory[0]["source_plant"] == "Cichorium intybus"
assert chicory[0]["identity_scope"] == "exact_species"

# Genus-level observations must never masquerade as exact species.
for row in observations:
    if "sp." in row["source_plant"] or row["source_plant"] in {"Taraxacum", "Sonchus", "Trifolium", "Medicago"}:
        assert row["identity_scope"] != "exact_species", row

# Bulgarian Sedum observations cannot be silently mapped to S. sarmentosum.
for taxon in {"Sedum rubens", "Sedum album"}:
    row = next(r for r in observations if r["source_plant"] == taxon)
    assert row["plant_id"] is None
    assert "Sedum sarmentosum" in row["mapping_note"]

for forbidden in ["feeding_frequency", "diet_percentage", "evidence_grade", "safe_unlimited"]:
    assert forbidden not in json.dumps(obj, ensure_ascii=False)

print(f"OK: {len(sources)} sources, {len(observations)} direct Ibera observations audited")
