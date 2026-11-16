import csv
import json
import tempfile
import unittest
from pathlib import Path
from scripts.export_tortoise_literature_review_csv import export_queue


class ReviewQueueExportTests(unittest.TestCase):
    def test_export_preserves_source_and_empty_verified_fields(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "input.jsonl"
            source.write_text(json.dumps({
                "source_database": "MED", "source_record_id": "123",
                "source_url": "https://europepmc.org/article/MED/123",
                "doi": "10.1000/example", "review_priority": "abstract_review",
                "review_status": "manual_validation_required", "feeding_verdict": None,
                "plant_diet_context_excerpts": ["Tortoise diet included leaves."],
                "unverified_binomial_strings": ["Taraxacum officinale"]
            }) + "\n")
            counts = export_queue(source, root / "review.csv")
            self.assertEqual(counts, {"review_rows": 1, "priority_rows": 1})
            with (root / "review.csv").open(encoding="utf-8-sig", newline="") as stream:
                row = next(csv.DictReader(stream))
            self.assertEqual(row["verified_plant_scientific_name"], "")
            self.assertEqual(row["source_record_id"], "123")

    def test_unverified_verdict_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "input.jsonl").write_text(json.dumps({
                "source_database": "MED", "source_record_id": "123",
                "review_status": "manual_validation_required", "feeding_verdict": "safe"
            }) + "\n")
            with self.assertRaises(ValueError):
                export_queue(root / "input.jsonl", root / "review.csv")
            self.assertFalse((root / "review.csv").exists())


if __name__ == "__main__":
    unittest.main()
