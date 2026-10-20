"""Check that taxonomy export matches the live all-plants catalog schema."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from export_public_taxonomy_search import export


def item(name="Bellis perennis", key="123", **kwargs):
    d = {
        "scientific": name,
        "taxon_id": key,
        "family": "Asteraceae",
        "feeding_status": "unverified",
        "feeding_grade": None,
        "publication_status": "staged_not_public",
    }
    d.update(kwargs)
    return d


class SearchExportTests(unittest.TestCase):
    def test_live_six_column_contract(self):
        result = export([item()])
        self.assertEqual(result["rows"], [["123", "Bellis perennis", "Asteraceae", "", "", False]])

    def test_rejects_unreviewed_safety_claim(self):
        with self.assertRaises(ValueError):
            export([item(feeding_grade="A")])
        with self.assertRaises(ValueError):
            export([item(feeding_status="reviewed")])

    def test_rejects_duplicate_taxon(self):
        with self.assertRaises(ValueError):
            export([item(), item(name="Achillea millefolium")])
        with self.assertRaises(ValueError):
            export([item(), item(name="bellis perennis", key="456")])

    def test_rejects_missing_taxon_identity(self):
        with self.assertRaises(ValueError):
            export([item(key="")])


if __name__ == "__main__":
    unittest.main()
