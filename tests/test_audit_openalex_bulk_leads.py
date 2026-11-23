"""Verify OpenAlex discovery metrics remain research-only and retry-safe."""
import json
import tempfile
import unittest
from pathlib import Path

from scripts.audit_openalex_bulk_leads import audit


class BulkLeadAuditTests(unittest.TestCase):
    def test_deduplication_and_retry_does_not_erase_success(self):
        rows = [
            {"name": "Plantago major", "status": "searched", "hits": [
                {"status": "literature_lead_unreviewed", "openalex_id": "https://openalex.org/W1"}]},
            {"name": "Plantago major", "status": "retry_needed", "hits": []},
            {"name": "Abies alba", "status": "searched", "hits": [
                {"status": "literature_lead_unreviewed", "openalex_id": "https://openalex.org/W1"}]},
            {"name": "Beta vulgaris", "status": "retry_needed", "hits": []},
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "leads.jsonl"
            path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
            result = audit(path)
        self.assertEqual(result["attempt_rows"], 4)
        self.assertEqual(result["unique_taxa_attempted"], 3)
        self.assertEqual(result["unique_taxa_searched"], 2)
        self.assertEqual(result["unique_taxa_retry_needed"], 1)
        self.assertEqual(result["total_hit_occurrences"], 2)
        self.assertEqual(result["distinct_identified_works"], 1)
        self.assertEqual(result["feeding_verdicts_confirmed"], 0)

    def test_rejects_promoted_feeding_claim(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "leads.jsonl"
            path.write_text(json.dumps({"name": "Plantago major", "status": "searched",
                                        "hits": [{"status": "feeding_verified"}]}) + "\n")
            with self.assertRaisesRegex(ValueError, "unreviewed evidence status violation"):
                audit(path)


if __name__ == "__main__":
    unittest.main()
