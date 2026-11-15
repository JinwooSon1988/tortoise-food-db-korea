"""Regression tests for the bulk integrity audit. Run: python -m unittest discover -s tests -p 'test_bulk_integrity.py'"""
import json
import tempfile
import unittest
from pathlib import Path
from scripts.audit_bulk_integrity import audit


class BulkAuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "data").mkdir()
        self.write("plants.json", [{"id": "a"}, {"id": "b"}])
        self.write("public_evidence_records.json", {"records": [
            {"id": "source1", "plant_ids": ["a"], "source_title": "Source", "url": "https://example.org/source"}
        ]})
        self.write("public_assessments.json", [
            {"plant_id": "a", "species_group": "Testudo", "verdict": "supported_mixed_diet", "evidence_ids": ["source1"]}
        ])

    def write(self, filename, value):
        (self.root / "data" / filename).write_text(json.dumps(value), encoding="utf-8")

    def test_valid_fixture(self):
        self.assertTrue(audit(self.root)["passed"])

    def test_duplicate_plant_id(self):
        self.write("plants.json", [{"id": "a"}, {"id": "a"}])
        self.assertIn("duplicate_id", {e["code"] for e in audit(self.root)["errors"]})

    def test_unknown_evidence_plant(self):
        self.write("public_evidence_records.json", {"records": [
            {"id": "source1", "plant_ids": ["missing"], "source_title": "Source", "url": "https://example.org/source"}
        ]})
        self.assertIn("unknown_evidence_plant", {e["code"] for e in audit(self.root)["errors"]})

    def test_missing_assessment_evidence(self):
        self.write("public_assessments.json", [
            {"plant_id": "a", "species_group": "Testudo", "verdict": "supported_mixed_diet", "evidence_ids": ["missing"]}
        ])
        self.assertIn("unknown_assessment_evidence", {e["code"] for e in audit(self.root)["errors"]})

    def test_positive_verdict_without_evidence(self):
        self.write("public_assessments.json", [
            {"plant_id": "a", "species_group": "Testudo", "verdict": "supported_mixed_diet", "evidence_ids": []}
        ])
        self.assertIn("positive_verdict_without_evidence", {e["code"] for e in audit(self.root)["errors"]})

    def test_duplicate_assessment(self):
        row = {"plant_id": "a", "species_group": "Testudo", "verdict": "hold", "evidence_ids": []}
        self.write("public_assessments.json", [row, row])
        self.assertIn("duplicate_assessment", {e["code"] for e in audit(self.root)["errors"]})

    def test_invalid_reference_types(self):
        self.write("public_evidence_records.json", {"records": [
            {"id": "source1", "plant_ids": "a", "source_title": "Source", "url": "https://example.org/source"}
        ]})
        self.write("public_assessments.json", [
            {"plant_id": "a", "species_group": "Testudo", "verdict": "supported_mixed_diet", "evidence_ids": "source1"}
        ])
        codes = {e["code"] for e in audit(self.root)["errors"]}
        self.assertIn("invalid_plant_ids", codes)
        self.assertIn("invalid_evidence_ids", codes)

    def test_large_batch_without_false_duplicates(self):
        count = 25000
        self.write("plants.json", [{"id": f"p{i:05d}"} for i in range(count)])
        self.write("public_evidence_records.json", {"records": [
            {"id": f"e{i:05d}", "plant_ids": [f"p{i:05d}"], "source_title": "Fixture only", "url": "https://example.org/fixture"}
            for i in range(count)
        ]})
        self.write("public_assessments.json", [
            {"plant_id": f"p{i:05d}", "species_group": "Testudo", "verdict": "hold", "evidence_ids": [f"e{i:05d}"]}
            for i in range(count)
        ])
        report = audit(self.root)
        self.assertTrue(report["passed"], report["errors"][:3])
        self.assertEqual(report["counts"]["plants"], count)

    def test_cross_plant_evidence_rejected(self):
        self.write("public_assessments.json", [
            {"plant_id": "b", "species_group": "Testudo", "verdict": "supported_mixed_diet", "evidence_ids": ["source1"]}
        ])
        codes = {e["code"] for e in audit(self.root)["errors"]}
        self.assertIn("evidence_not_linked_to_assessed_plant", codes)

    def test_coverage_metrics_and_orphan_warning(self):
        self.write("public_assessments.json", [])
        report = audit(self.root)
        self.assertTrue(report["passed"])
        self.assertEqual(report["counts"]["plants_without_assessments"], 2)
        self.assertEqual(report["counts"]["evidence_unreferenced"], 1)
        self.assertIn("unreferenced_evidence", {w["code"] for w in report["warnings"]})

    def test_duplicate_source_warning_preserves_records(self):
        self.write("public_evidence_records.json", {"records": [
            {"id": "source1", "plant_ids": ["a"], "source_title": "Study", "url": "https://example.org/study"},
            {"id": "source2", "plant_ids": ["a"], "source_title": "Study", "url": "https://example.org/study/"},
        ]})
        report = audit(self.root)
        self.assertTrue(report["passed"])
        self.assertEqual(report["counts"]["same_source_same_plant_pairs"], 1)
        self.assertIn("same_source_same_plant", {w["code"] for w in report["warnings"]})


if __name__ == "__main__":
    unittest.main()
