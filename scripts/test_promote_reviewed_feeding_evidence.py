#!/usr/bin/env python3
"""Offline tests for promote_reviewed_feeding_evidence.py: only reviewer-approved records read in the original are
promoted, legacy type names map to the site's types, incomplete records are rejected, and the Batch 002 site
index is never written. Uses temporary files only."""
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/promote_reviewed_feeding_evidence.py"
GOOD = {"reviewed": True, "reviewer": "Test Reviewer", "original_inspected": True, "scientific": "Opuntia ficus-indica",
        "source_url": "https://doi.org/10.0000/example", "citation": "Example, A. (2020) Diet of tortoises. J. Test 1:1-9",
        "tortoise": "Testudo graeca", "type": "captive_feeding_report", "locator": "Table 2, p. 4",
        "plant_part": {"ko": "줄기마디(패드)", "en": "pad"}, "finding": {"ko": "사육 개체가 먹음", "en": "Eaten by captive tortoises"}, "source_class": "peer_reviewed", "evidence_basis": "original_study"}


class PromoteTests(unittest.TestCase):
    def run_with(self, records):
        tmp = Path(tempfile.mkdtemp())
        (tmp / "approved.json").write_text(json.dumps({"records": records}), encoding="utf-8")
        r = subprocess.run([sys.executable, "-X", "utf8", str(SCRIPT), "--approved", str(tmp / "approved.json"),
                            "--output", str(tmp / "reviewed-records.json"), "--report", str(tmp / "report.json")],
                           capture_output=True, text=True)
        report = json.loads((tmp / "report.json").read_text(encoding="utf-8"))
        out = tmp / "reviewed-records.json"
        return r.returncode, report, json.loads(out.read_text(encoding="utf-8")) if out.exists() else None

    def test_good_record_promoted_and_legacy_type_mapped(self):
        code, report, batch = self.run_with([GOOD])
        self.assertEqual(code, 0)
        self.assertEqual(report["promoted"], 1)
        self.assertEqual(report["type_names_mapped"], [{"record": 0, "from": "captive_feeding_report", "to": "captive_feeding_record"}])
        rec = batch["records"][0]
        self.assertEqual((rec["type"], rec["verification"]), ("captive_feeding_record", "reviewed_source_record"))
        self.assertTrue(batch["sources"][0]["url"].startswith("https://") and batch["sources"][0]["study_id"])

    def test_unreviewed_or_not_read_or_incomplete_rejected(self):
        bad = [dict(GOOD, reviewed=False), dict(GOOD, original_inspected=False), dict(GOOD, reviewer=""),
               dict(GOOD, tortoise="tortoise"), dict(GOOD, plant_part={"ko": "", "en": "pad"}), dict(GOOD, source_url="ftp://x/y"),
               dict(GOOD, type="nutritional_analysis"), dict(GOOD, type="safe_to_feed"), dict(GOOD, scientific="Opuntia"),
               dict(GOOD, scientific="Notaplant inventedii"), dict(GOOD, source_class=None), dict(GOOD, source_class="keeper_community"),
               dict(GOOD, evidence_basis=None)]
        code, report, batch = self.run_with(bad)
        self.assertEqual(code, 2)
        self.assertEqual((report["promoted"], report["rejected"]), (0, len(bad)))
        self.assertIsNone(batch)

    def test_review_basis_is_not_counted_as_the_original(self):
        code, report, batch = self.run_with([dict(GOOD, evidence_basis="review_or_species_account")])
        self.assertEqual((code, batch["records"][0]["verification"]), (0, "review_full_text_verified"))

    def test_one_rejected_record_publishes_nothing(self):
        code, report, batch = self.run_with([GOOD, dict(GOOD, reviewed=False)])
        self.assertEqual((code, report["promoted"], report["rejected"]), (2, 0, 1))
        self.assertIsNone(batch)

    def test_keeper_report_stays_unverified(self):
        code, report, batch = self.run_with([dict(GOOD, source_class="keeper_community", type="community_report")])
        self.assertEqual(code, 0)
        rec = batch["records"][0]
        self.assertEqual((rec["type"], rec["verification"], rec["identification"]), ("community_report", "community_report_unverified", "binomial_in_source"))

    def test_batch_002_index_untouched(self):
        idx = ROOT / "data/catalog-evidence/batch-002-site-index.json"
        before = hashlib.sha256(idx.read_bytes()).hexdigest()
        self.run_with([GOOD])
        self.assertEqual(hashlib.sha256(idx.read_bytes()).hexdigest(), before)


if __name__ == "__main__":
    unittest.main(verbosity=1)
