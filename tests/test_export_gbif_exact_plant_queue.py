import unittest
from scripts.export_gbif_exact_plant_queue import build_queue


class BulkExactQueueTests(unittest.TestCase):
    def test_exact_only_deduplicated_and_unverified(self):
        base = dict(openalex_id="https://openalex.org/W123",
                    candidate_binomial="Plantago major",
                    gbif_status="exact_plant_taxon_candidate",
                    gbif_taxon_key="1234", gbif_scientific_name="Plantago major L.",
                    feeding_keyword_windows="3", sample_context="Plantago major")
        rows = [base, base, {**base, "gbif_status": "not_exact_plant_match"},
                {**base, "openalex_id": "https://openalex.org/W456", "feeding_keyword_windows": "0"}]
        queue = build_queue(rows)
        self.assertEqual(len(queue), 1)
        self.assertEqual(queue[0]["unique_papers"], 2)
        self.assertEqual(queue[0]["feeding_keyword_papers"], 1)
        self.assertEqual(queue[0]["feeding_confirmed"], "unverified")
        self.assertEqual(queue[0]["safety_verdict"], "not_assessed")


if __name__ == "__main__":
    unittest.main()
