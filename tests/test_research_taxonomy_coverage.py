import csv
import json
import tempfile
import unittest
from pathlib import Path

from scripts.report_research_taxonomy_coverage import coverage


class ResearchCoverageTests(unittest.TestCase):
    def test_full_taxonomy_coverage_and_no_safety_inference(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            taxa = root / "taxa.csv"
            taxa.write_text("plant_scientific_name\nPlantago major\nTaraxacum officinale\n")
            abstract = root / "abstract.jsonl"
            abstract.write_text(json.dumps({
                "plant_scientific_name": "Plantago major", "source_scope": "abstract",
                "review_status": "unverified_abstract_mention",
                "source_database": "MED", "source_record_id": "123",
                "feeding_verdict": None}) + "\n")
            result = coverage(taxa, abstract, None, root / "coverage.csv", root / "report.json")
            self.assertEqual(result["taxonomy_species"], 2)
            self.assertEqual(result["species_with_unverified_mentions"], 1)
            self.assertEqual(result["species_without_exact_mentions"], 1)
            with (root / "coverage.csv").open(newline="") as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(len(rows), 2)
            self.assertEqual({row["feeding_verdict"] for row in rows}, {""})
            with self.assertRaises(ValueError):
                coverage(taxa, abstract, None, root / "coverage.csv", root / "report.json")

    def test_rejects_unsupported_mention_and_duplicate_taxa(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            taxa = root / "taxa.csv"
            abstract = root / "abstract.jsonl"
            taxa.write_text("plant_scientific_name\nPlantago major\nPlantago major\n")
            abstract.write_text("")
            with self.assertRaises(ValueError):
                coverage(taxa, abstract, None, root / "coverage.csv", root / "report.json")
            taxa.write_text("plant_scientific_name\nPlantago major\n")
            abstract.write_text(json.dumps({"plant_scientific_name": "Other species",
                "source_scope": "abstract", "review_status": "unverified_abstract_mention",
                "source_database": "MED", "source_record_id": "1", "feeding_verdict": None}) + "\n")
            with self.assertRaises(ValueError):
                coverage(taxa, abstract, None, root / "coverage.csv", root / "report.json")


if __name__ == "__main__":
    unittest.main()
