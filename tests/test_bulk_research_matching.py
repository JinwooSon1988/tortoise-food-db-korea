import csv
import json
import tempfile
import unittest
from pathlib import Path
from scripts.run_bulk_research_matching import run


class BulkResearchMatchingTests(unittest.TestCase):
    def test_single_batch_matches_accepted_taxa_without_verdicts(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            catalog = root / "plants.json"
            accepted = root / "accepted.csv"
            abstracts = root / "abstracts.jsonl"
            fulltexts = root / "fulltexts.jsonl"
            catalog.write_text(json.dumps([{"scientific": "Plantago major"}]))
            with accepted.open("w", newline="") as stream:
                writer = csv.writer(stream)
                writer.writerow(["plant_scientific_name", "taxonomic_status", "source_reference"])
                writer.writerow(["Taraxacum officinale", "accepted", "taxon-source-1"])
            record = {"source_database": "MED", "source_record_id": "123",
                      "review_status": "unmatched_literature_lead",
                      "feeding_verdict": None, "source_url": "https://example.org/123",
                      "abstract_text": "Plantago major and Taraxacum officinale are mentioned."}
            abstracts.write_text(json.dumps(record) + "\n")
            fulltexts.write_text(json.dumps({**record, "abstract_text":
                "Taraxacum officinale is discussed in a tortoise diet paper."}) + "\n")
            result = run(catalog, accepted, abstracts, fulltexts, root / "output")
            self.assertEqual(result["taxonomy"]["unique_binomials"], 2)
            self.assertEqual(result["abstracts"]["unverified_plant_publication_links"], 2)
            self.assertEqual(result["fulltexts"]["unverified_plant_publication_links"], 1)
            for name in ("abstract-mentions.jsonl", "fulltext-mentions.jsonl"):
                rows = [json.loads(line) for line in (root / "output" / name).read_text().splitlines()]
                self.assertTrue(all(row["feeding_verdict"] is None for row in rows))
            with self.assertRaises(ValueError):
                run(catalog, accepted, abstracts, fulltexts, root / "output")

    def test_missing_input_does_not_create_output(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with self.assertRaises(FileNotFoundError):
                run(root / "missing.json", root / "accepted.csv",
                    root / "abstracts.jsonl", None, root / "output")
            self.assertFalse((root / "output").exists())


if __name__ == "__main__":
    unittest.main()
