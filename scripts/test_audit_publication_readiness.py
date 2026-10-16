#!/usr/bin/env python3
"""Offline regression for publication audit, including strict taxonomy-only quarantine."""
import importlib.util
from pathlib import Path
root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("audit", root / "scripts/audit_publication_readiness.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
plants = [{"id": "a"}, {"id": "b"}]
assessments = [{"plant_id": "a", "verdict": "supported_mixed_diet",
                "evidence_ids": ["e1"], "animal_taxon": "Testudo", "limits": ["mixed only"]},
               {"plant_id": "b", "verdict": "supported_mixed_diet", "evidence_ids": ["missing"]}]
records = [{"id": "e1", "source_type": "academic_study", "directness": "direct"}]
result = mod.audit(plants, assessments, records,
                   [{"candidate_id": "gbif_1", "feeding_verdict": None},
                    {"candidate_id": "gbif_2", "feeding_verdict": "safe"}])
assert result["summary"]["assessment_rows_with_linked_evidence"] == 1
assert result["summary"]["taxonomy_only_candidates"] == 1
assert result["summary"]["issues"] == 2
assert result["existing_reviewed"][0]["direct_evidence_count"] == 1
assert any(x["reason"] == "unsafe_taxonomy_verdict" for x in result["issues"])
print("Publication readiness regression: PASS")
