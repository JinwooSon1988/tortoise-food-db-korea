import csv
import tempfile
import unittest
from pathlib import Path
from scripts.import_reviewed_tortoise_literature import convert


class ReviewedImportTests(unittest.TestCase):
    def write_csv(self, path, rows):
        with path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=rows[0])
            writer.writeheader()
            writer.writerows(rows)

    def write_corpus(self, path):
        import json
        path.write_text(json.dumps({
            "source_database": "MED", "source_record_id": "123",
            "title": "Diet observation",
            "source_url": "https://europepmc.org/article/MED/123",
            "abstract_text": "Tortoises were observed eating the leaves of this species."
        }) + "\\n")

    def test_unreviewed_cannot_be_imported(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_csv(root / "input.csv", [{"review_status": "manual_validation_required"}])
            self.write_corpus(root / "corpus.jsonl")
            with self.assertRaises(ValueError):
                convert(root / "input.csv", root / "out.jsonl", root / "corpus.jsonl")
            self.assertFalse((root / "out.jsonl").exists())

    def test_reviewed_observation_remains_unpublished(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_csv(root / "input.csv", [{
                "review_status": "reviewed_observation",
                "verified_plant_scientific_name": "Taraxacum officinale",
                "verified_tortoise_scientific_name": "Testudo graeca",
                "verified_plant_part": "leaves",
                "observation_type": "observed_ingestion",
                "evidence_quote": "Tortoises were observed eating the leaves of this species.",
                "source_title": "Diet observation", "reviewer_notes": "Checked primary paper",
                "source_record_id": "123", "source_database": "MED",
                "source_url": "https://europepmc.org/article/MED/123",
                "reviewed_at": "2026-11-16"}])
            self.write_corpus(root / "corpus.jsonl")
            self.assertEqual(convert(root / "input.csv", root / "out.jsonl", root / "corpus.jsonl")["public_feeding_verdicts"], 0)
            import json
            row = json.loads((root / "out.jsonl").read_text())
            self.assertIsNone(row["feeding_verdict"])
            self.assertEqual(row["review_status"], "reviewed_observation_unverified_for_publication")


if __name__ == "__main__":
    unittest.main()
