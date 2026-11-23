"""Offline regression tests for large research-only candidate CSV intake."""
import tempfile
import unittest
from pathlib import Path

from scripts.research_bulk_leads import load_candidate_csv


class BulkCandidateCsvTests(unittest.TestCase):
    def test_deduplicates_streamed_candidates(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "candidates.csv"
            path.write_text(
                "plant_scientific_name\nPlantago major\nAbies alba\nPlantago major\n",
                encoding="utf-8",
            )
            self.assertEqual(
                [row["name"] for row in load_candidate_csv(path)],
                ["Plantago major", "Abies alba"],
            )
            self.assertTrue(all(row["taxon_id"] is None for row in load_candidate_csv(path)))

    def test_rejects_missing_column_and_invalid_binomial(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "candidates.csv"
            for contents in (
                "name\nPlantago major\n",
                "plant_scientific_name\nPlantago major; DROP TABLE\n",
                "plant_scientific_name\n123 invalid\n",
            ):
                with self.subTest(contents=contents):
                    path.write_text(contents, encoding="utf-8")
                    with self.assertRaises(ValueError):
                        list(load_candidate_csv(path))


if __name__ == "__main__":
    unittest.main()
