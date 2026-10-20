"""Regression tests for high-volume taxonomy staging (no food safety assertions)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_bulk_taxon_catalog import BINOMIAL, stage


def row(name, *, rank="species", status="accepted", kingdom="Plantae", key="123"):
    return {
        "scientificName": name,
        "taxonRank": rank,
        "taxonomicStatus": status,
        "kingdom": kingdom,
        "gbifID": key,
        "datasetKey": "dataset-test",
    }


class BulkCatalogTests(unittest.TestCase):
    def test_infraspecific_names(self):
        self.assertIsNotNone(BINOMIAL.fullmatch("Testudo plantus subsp. minor"))
        self.assertIsNotNone(BINOMIAL.fullmatch("Testudo plantus var. minor"))
        self.assertIsNone(BINOMIAL.fullmatch("Testudo plantus subspX minor"))

    def test_dedup_and_existing(self):
        rows = [row("Cichorium intybus"), row("Bellis perennis"),
                row("Bellis perennis", key="124")]
        got, rejected = stage(rows, [{"scientific": "Cichorium intybus"}])
        self.assertEqual([x["scientific"] for x in got], ["Bellis perennis"])
        self.assertEqual(rejected["already_in_public_catalog"], 1)
        self.assertEqual(rejected["duplicate_taxon"], 1)
        self.assertIsNone(got[0]["feeding_grade"])

    def test_no_invented_taxonomy_or_feeding_evidence(self):
        rows = [row("Bellis perennis", status="synonym"),
                row("Bellis perennis", kingdom="Animalia"),
                row("Bellis perennis", key=""),
                row("Bellis perennis")]
        got, rejected = stage(rows, [])
        self.assertEqual(len(got), 1)
        self.assertEqual(got[0]["feeding_status"], "unverified")
        self.assertEqual(got[0]["feeding_evidence_ids"], [])
        self.assertEqual(got[0]["publication_status"], "staged_not_public")
        self.assertEqual(rejected["not_accepted_taxon"], 1)
        self.assertEqual(rejected["not_verified_plantae"], 1)
        self.assertEqual(rejected["missing_traceable_taxon_source"], 1)

    def test_subspecies_is_distinct_from_species(self):
        rows = [row("Plantago major"), row("Plantago major subsp. intermedia", rank="subspecies")]
        got, _ = stage(rows, [])
        self.assertEqual(len(got), 2)


if __name__ == "__main__":
    unittest.main()
