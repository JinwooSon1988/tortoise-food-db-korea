import unittest
from unittest.mock import patch
from scripts.discover_tortoise_diet_literature import combine, search, QUERIES

class TortoiseDietDiscoveryTests(unittest.TestCase):
    def test_query_matrix_covers_tortoise_and_genera(self):
        self.assertGreaterEqual(len(QUERIES), 10)
        self.assertTrue(any("Testudo" in q for q in QUERIES))
        self.assertTrue(any("Gopherus" in q for q in QUERIES))

    def test_deduplicates_doi_and_never_verifies_feeding(self):
        hit = {"doi": "10.1000/example", "title": "A diet paper",
               "pmcid": "PMC123", "pubYear": "2024"}
        result = combine([
            {"query": "one", "status": "ok", "records": [hit]},
            {"query": "two", "status": "ok", "records": [hit]},
            {"query": "three", "status": "error", "records": []}])
        self.assertEqual(result["unique_sources"], 1)
        self.assertEqual(result["queries_failed"], 1)
        row = result["records"][0]
        self.assertEqual(row["matched_queries"], ["one", "two"])
        self.assertEqual(row["feeding_safety_status"], "unassessed")
        self.assertEqual(row["feeding_observation_status"], "not_verified")
        self.assertEqual(row["verified_plant_links"], [])

    def test_failed_provider_is_reported_not_silent(self):
        with patch("scripts.discover_tortoise_diet_literature.urllib.request.urlopen",
                   side_effect=OSError("offline")):
            with patch("scripts.discover_tortoise_diet_literature.time.sleep"):
                result = search(QUERIES[0], retries=1)
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["records"], [])

if __name__ == "__main__":
    unittest.main()
