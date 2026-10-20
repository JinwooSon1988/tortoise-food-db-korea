#!/usr/bin/env python3
"""Regression tests for read-only held/public evidence overlap audit."""
import json
import tempfile
import unittest
from pathlib import Path

from audit_public_evidence_blocked_overlap import audit


class AuditBlockedOverlapTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "data").mkdir()
        self.write("feeding_p1_blocked_claim_manifest_20261018.json", {
            "blocked_claims": [
                {"status": "hold", "evidence_ids": ["e1"], "plant_id": "p1", "reason": "locator not checked"},
                {"status": "hold", "evidence_ids": ["e1", "e2"], "plant_id": "p2", "reason": "locator not checked"},
                {"status": "released", "evidence_ids": ["e3"], "plant_id": "p3"},
            ]
        })
        self.write("public_evidence_records.json", {
            "records": [
                {"id": "e1", "plant_ids": ["p1", "p2"], "directness": "direct"},
                {"id": "e3", "plant_ids": ["p3"], "directness": "direct"},
            ]
        })
        self.write("reviewed_plant_reverse_evidence_index.json", {
            "records": [
                {"plant_id": "p1", "public_sources": [{"id": "e1"}]},
                {"plant_id": "p2", "public_sources": [{"id": "e1"}]},
            ]
        })

    def tearDown(self):
        self.temp.cleanup()

    def write(self, name, obj):
        (self.root / "data" / name).write_text(json.dumps(obj), encoding="utf-8")

    def test_deduplicates_overlaps_but_preserves_held_claims(self):
        result = audit(self.root)
        self.assertEqual(result["blocked_claim_rows"], 3)
        self.assertEqual(result["unique_held_evidence_ids"], 2)
        self.assertEqual(result["overlap_count"], 1)
        finding = result["findings"][0]
        self.assertEqual(finding["evidence_id"], "e1")
        self.assertEqual(finding["reverse_plant_ids"], ["p1", "p2"])
        self.assertEqual(len(finding["held_claims"]), 2)

    def test_no_public_overlap(self):
        self.write("public_evidence_records.json", {"records": [{"id": "e3"}]})
        result = audit(self.root)
        self.assertEqual(result["overlap_count"], 0)

    def test_read_only(self):
        files = list((self.root / "data").glob("*.json"))
        before = {p.name: p.read_bytes() for p in files}
        audit(self.root)
        self.assertEqual(before, {p.name: p.read_bytes() for p in files})


if __name__ == "__main__":
    unittest.main()
