#!/usr/bin/env python3
"""Regression: bulk GBIF candidate review must prefer relevant context without promoting safety."""
import unittest
from export_gbif_exact_plant_queue import build_queue


class BulkQueueTests(unittest.TestCase):
    def test_dedup_prefers_feeding_keyword_context_without_safety_promotion(self):
        base = {"candidate_binomial": "Nasturtium officinale",
                "gbif_status": "exact_plant_taxon_candidate",
                "gbif_taxon_key": "123", "gbif_scientific_name": "Nasturtium officinale"}
        rows = [
            dict(base, openalex_id="https://openalex.org/W123", feeding_keyword_windows="0",
                 sample_context="Unrelated abstract mention"),
            dict(base, openalex_id="https://openalex.org/W456", feeding_keyword_windows="2",
                 sample_context="Candidate feeding mention; requires original-source review"),
            dict(base, openalex_id="https://openalex.org/W456", feeding_keyword_windows="2",
                 sample_context="Duplicate mention"),
            dict(base, openalex_id="https://openalex.org/W789", feeding_keyword_windows="0",
                 sample_context="Other source"),
        ]
        queue = build_queue(rows)
        self.assertEqual(len(queue), 1)
        item = queue[0]
        self.assertEqual(item["unique_papers"], 3)
        self.assertEqual(item["feeding_keyword_papers"], 1)
        self.assertEqual(item["sample_context"], rows[1]["sample_context"])
        self.assertEqual(item["feeding_confirmed"], "unverified")
        self.assertEqual(item["safety_verdict"], "not_assessed")
        self.assertEqual(item["full_text_checked"], "no")

    def test_excludes_nonexact_taxonomy_and_invalid_identifiers(self):
        row = {"candidate_binomial": "Test plant", "gbif_taxon_key": "42",
               "gbif_scientific_name": "Test plant", "openalex_id": "https://openalex.org/W42",
               "feeding_keyword_windows": "1", "sample_context": "Candidate"}
        self.assertEqual(build_queue([dict(row, gbif_status="fuzzy_match")]), [])
        self.assertEqual(build_queue([dict(row, gbif_status="exact_plant_taxon_candidate",
                                           gbif_taxon_key="unknown")]), [])


if __name__ == "__main__":
    unittest.main()
