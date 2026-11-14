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


if __name__ == "__main__":
    unittest.main()
