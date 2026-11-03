#!/usr/bin/env python3
"""Regression tests for source-review batch merging and fail-closed provenance."""
import copy
import unittest
from scripts.merge_source_review_results import merge

URL = "https://doi.org/10.1234/example"
QUEUE = {"records": [{"source_url": URL, "taxon_associations": [{"taxon_id": "gbif:1"}]}]}
BASE = {"source_url": URL, "review_status": "pending", "feeding_safety_status": "unassessed",
        "verified_plant_links": []}
LINK = {"taxon_id": "gbif:1", "verbatim_plant_name": "Plantus example",
        "evidence_locator": "Table 1, row 3", "observed_animal_taxon": "Testudo graeca",
        "observed_plant_part": "leaf", "feeding_safety_status": "unassessed"}

class ReviewMergeTests(unittest.TestCase):
    def run_merge(self, *records):
        return merge(QUEUE, [{"records": [r]} for r in records])

    def test_pending_is_safe(self):
        result = self.run_merge(copy.deepcopy(BASE))
        self.assertEqual(result["plant_links_verified"], 0)

    def test_verified_link_requires_provenance(self):
        row = {**BASE, "review_status": "plant_links_reviewed", "verified_plant_links": [copy.deepcopy(LINK)]}
        self.assertEqual(self.run_merge(row)["plant_links_verified"], 1)
        for key in ("verbatim_plant_name", "evidence_locator", "observed_animal_taxon", "observed_plant_part"):
            broken = copy.deepcopy(row)
            broken["verified_plant_links"][0].pop(key)
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.run_merge(broken)

    def test_rejects_duplicate_sources(self):
        with self.assertRaises(ValueError):
            self.run_merge(copy.deepcopy(BASE), copy.deepcopy(BASE))

    def test_rejects_unsupported_taxa(self):
        row = {**BASE, "review_status": "plant_links_reviewed",
               "verified_plant_links": [{**LINK, "taxon_id": "gbif:999"}]}
        with self.assertRaises(ValueError):
            self.run_merge(row)

    def test_rejects_safety_promotion(self):
        row = {**BASE, "feeding_safety_status": "safe"}
        with self.assertRaises(ValueError):
            self.run_merge(row)
        row = {**BASE, "review_status": "plant_links_reviewed",
               "verified_plant_links": [{**LINK, "feeding_safety_status": "safe"}]}
        with self.assertRaises(ValueError):
            self.run_merge(row)

    def test_rejects_empty_verified_status(self):
        with self.assertRaises(ValueError):
            self.run_merge({**BASE, "review_status": "plant_links_reviewed"})

if __name__ == "__main__":
    unittest.main()
