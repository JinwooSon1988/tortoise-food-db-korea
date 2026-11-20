import json
import tempfile
import unittest
from pathlib import Path
from scripts.prepare_fulltext_plant_matching import convert
from scripts.link_plant_abstract_mentions import link


class FulltextPlantMatchingTests(unittest.TestCase):
    def test_large_fulltext_batch_streams_all_rows_in_order(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "fulltexts.jsonl"
            with source.open("w", encoding="utf-8") as stream:
                for number in range(150):
                    stream.write(json.dumps({
                        "source_database": "PMC", "source_record_id": f"PMC{number}",
                        "source_url": f"https://europepmc.org/article/PMC/PMC{number}",
                        "source_title": f"Study {number}",
                        "fulltext_excerpt": "Plantago major " + "x" * 12000,
                        "review_status": "unverified_fulltext_for_manual_review",
                        "feeding_verdict": None
                    }) + "\n")
            result = convert(source, root / "prepared.jsonl")
            self.assertEqual(result["fulltexts_prepared"], 150)
            with (root / "prepared.jsonl").open(encoding="utf-8") as stream:
                rows = [json.loads(line) for line in stream]
            self.assertEqual(len(rows), 150)
            self.assertEqual(rows[0]["source_record_id"], "PMC0")
            self.assertEqual(rows[-1]["source_record_id"], "PMC149")
            self.assertTrue(all(row["feeding_verdict"] is None for row in rows))

    def test_invalid_late_record_never_publishes_partial_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            valid = {"source_database": "PMC", "source_record_id": "PMC1",
                     "source_url": "https://europepmc.org/article/PMC/PMC1",
                     "fulltext_excerpt": "Plantago major",
                     "review_status": "unverified_fulltext_for_manual_review",
                     "feeding_verdict": None}
            invalid = {**valid, "source_record_id": "PMC2",
                       "feeding_verdict": "safe"}
            source = root / "fulltexts.jsonl"
            source.write_text(json.dumps(valid) + "\n" + json.dumps(invalid) + "\n")
            with self.assertRaises(ValueError):
                convert(source, root / "prepared.jsonl")
            self.assertFalse((root / "prepared.jsonl").exists())

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
                          root / "mentions.jsonl", root / "report.json", source_scope="fulltext")
            self.assertEqual(result["unverified_plant_publication_links"], 1)
            row = json.loads((root / "mentions.jsonl").read_text())
            self.assertIsNone(row["feeding_verdict"])
            self.assertEqual(row["review_status"], "unverified_fulltext_mention")
            self.assertEqual(row["source_scope"], "fulltext")
            self.assertIn("Plantago major", row["mention_context"])


if __name__ == "__main__":
    unittest.main()
