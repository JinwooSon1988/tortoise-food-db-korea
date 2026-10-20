"""Synthetic 10,000-record performance and correctness regression test."""
import json
import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_bulk_taxon_catalog import stage
from build_taxonomy_directory import build


class BulkScaleTests(unittest.TestCase):
    def test_ten_thousand_taxa_without_feeding_verdicts(self):
        # Synthetic fixtures test capacity only, never publish as real taxa.
        rows = []
        for i in range(10000):
            name = self._letters(i)
            rows.append({
                "canonicalName": "Genus " + name,
                "taxonRank": "species",
                "taxonomicStatus": "accepted",
                "kingdom": "Plantae",
                "gbifID": str(i + 1),
                "datasetKey": "synthetic-test-only",
                "family": "Testaceae",
            })
        start = time.monotonic()
        staged, rejected = stage(rows, [])
        self.assertEqual(len(staged), 10000, rejected)
        self.assertTrue(all(x["feeding_grade"] is None for x in staged))
        page = build(staged)
        self.assertIn("급여 안전성 미확정", page)
        self.assertIn("Genus ", page)
        self.assertLess(time.monotonic() - start, 30.0)

    @staticmethod
    def _letters(value):
        # Valid alphabetic epithets, deterministic and collision-free.
        chars = []
        value += 1
        while value:
            value, remainder = divmod(value - 1, 26)
            chars.append(chr(97 + remainder))
        return "a" + "".join(reversed(chars))


if __name__ == "__main__":
    unittest.main()
