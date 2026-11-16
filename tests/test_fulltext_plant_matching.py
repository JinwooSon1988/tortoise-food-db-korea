import json
import tempfile
import unittest
from pathlib import Path
from scripts.prepare_fulltext_plant_matching import convert
from scripts.link_plant_abstract_mentions import link


class FulltextPlantMatchingTests(unittest.TestCase):
    def test_fulltext_to_exact_matching_preserves_review_only(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "fulltexts.jsonl").write_text(json.dumps({
                "source_database": "PMC", "source_record_id": "PMC123",
                "source_url": "https://europepmc.org/article/PMC/PMC123",
                "source_title": "Tortoise study",
                "fulltext_excerpt": "The diet table lists Plantago major in a survey.",
                "review_status": "unverified_fulltext_for_manual_review",
                "feeding_verdict": None}) + "\n")
            self.assertEqual(convert(root / "fulltexts.jsonl", root / "match.jsonl")["fulltexts_prepared"], 1)
            (root / "taxa.csv").write_text("plant_scientific_name\nPlantago major\n")
            result = link(root / "match.jsonl", root / "taxa.csv",
                          root / "mentions.jsonl", root / "report.json")
            self.assertEqual(result["unverified_plant_publication_links"], 1)
            row = json.loads((root / "mentions.jsonl").read_text())
            self.assertIsNone(row["feeding_verdict"])
            self.assertEqual(row["review_status"], "unverified_abstract_mention")


if __name__ == "__main__":
    unittest.main()
