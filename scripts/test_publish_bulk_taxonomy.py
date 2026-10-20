"""Integration tests for taxonomy import -> searchable HTML generation."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from publish_bulk_taxonomy import execute


def taxon(name, key):
    return {
        "scientificName": name,
        "taxonRank": "species",
        "taxonomicStatus": "accepted",
        "kingdom": "Plantae",
        "gbifID": key,
        "datasetKey": "gbif-dataset-example",
        "family": "Asteraceae",
    }


class PipelineTests(unittest.TestCase):
    def test_end_to_end_and_hold_status(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            inp = base / "source.json"
            plants = base / "plants.json"
            staged = base / "staged.json"
            page = base / "taxonomy" / "index.html"
            search = base / "data" / "plant-catalog" / "search.json"
            inp.write_text(json.dumps([taxon("Bellis perennis", "1"),
                                       taxon("Bellis perennis", "2"),
                                       taxon("Cichorium intybus", "3"),
                                       taxon("Achillea millefolium", "4")]), encoding="utf-8")
            plants.write_text(json.dumps([{"scientific": "Cichorium intybus"}]), encoding="utf-8")
            report = execute(inp, staged, page, plants, minimum=2, search_path=search)
            self.assertEqual(report["new_taxonomy_only_records"], 2)
            self.assertEqual(report["feeding_verdicts_added"], 0)
            self.assertEqual(report["total_searchable_if_linked"], 3)
            data = json.loads(staged.read_text(encoding="utf-8"))
            self.assertEqual(len(data["records"]), 2)
            self.assertIn("급여 안전성 미확정", page.read_text(encoding="utf-8"))
            self.assertIn("Achillea millefolium", page.read_text(encoding="utf-8"))
            exported = json.loads(search.read_text(encoding="utf-8"))
            self.assertEqual(len(exported["rows"]), 2)
            self.assertTrue(all(len(row) == 6 and row[5] is False for row in exported["rows"]))

    def test_minimum_prevents_partial_publish(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            inp = base / "source.json"
            plants = base / "plants.json"
            staged = base / "staged.json"
            page = base / "taxonomy.html"
            inp.write_text(json.dumps([taxon("Bellis perennis", "1")]), encoding="utf-8")
            plants.write_text("[]", encoding="utf-8")
            with self.assertRaises(ValueError):
                execute(inp, staged, page, plants, minimum=10000, search_path=base / "search.json")
            self.assertFalse(staged.exists())
            self.assertFalse(page.exists())
            self.assertFalse((base / "search.json").exists())


if __name__ == "__main__":
    unittest.main()
