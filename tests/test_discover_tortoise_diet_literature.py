import unittest
from unittest.mock import patch
from scripts.discover_tortoise_diet_literature import combine, search, QUERIES, uniform_provider_outage, title_signal, crossref_fallback

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

    def test_title_ranking_excludes_tortoise_beetle_false_positive(self):
        self.assertEqual(title_signal("Tortoise beetle feeding on leaves"), "other_title")
        self.assertEqual(title_signal("Testudo graeca diet composition"), "tortoise_diet_title")
        self.assertEqual(title_signal("Gopherus habitat distribution"), "tortoise_title")
        hits = [
            {"doi": "10.1000/other", "title": "Tortoise beetle feeding"},
            {"doi": "10.1000/diet", "title": "Testudo graeca diet composition"}]
        result = combine([{"query": "q", "status": "ok", "records": hits}])
        self.assertEqual(result["records"][0]["source_key"], "doi:10.1000/diet")
        self.assertEqual(result["title_signal_counts"]["tortoise_diet_title"], 1)
        self.assertEqual(result["title_signal_counts"]["other_title"], 1)
        self.assertTrue(all(r["feeding_safety_status"] == "unassessed"
                            for r in result["records"]))

    def test_crossref_fallback_keeps_only_tortoise_diet_titles(self):
        import io
        import json
        response = {"message": {"items": [
            {"DOI": "10.1000/a", "title": ["Testudo graeca diet ecology"]},
            {"DOI": "10.1000/b", "title": ["Tortoise beetle feeding ecology"]}]}}
        class Response(io.BytesIO):
            def __enter__(self):
                return self
            def __exit__(self, *args):
                self.close()
        with patch("scripts.discover_tortoise_diet_literature.urllib.request.urlopen",
                   side_effect=lambda *a, **k: Response(json.dumps(response).encode())):
            rows = crossref_fallback(["Testudo diet"], workers=1)
        self.assertEqual(rows[0]["provider"], "crossref")
        self.assertEqual(len(rows[0]["records"]), 1)
        self.assertEqual(rows[0]["records"][0]["doi"], "10.1000/a")

    def test_uniform_503_opens_circuit_but_mixed_results_do_not(self):
        errors = [{"status": "error", "http_status": 503}] * 3
        self.assertTrue(uniform_provider_outage(errors))
        self.assertFalse(uniform_provider_outage(errors[:2]))
        self.assertFalse(uniform_provider_outage(errors[:2] + [
            {"status": "ok", "records": []}]))
        self.assertFalse(uniform_provider_outage(errors[:2] + [
            {"status": "error", "http_status": 500}]))

    def test_failed_provider_is_reported_not_silent(self):
        with patch("scripts.discover_tortoise_diet_literature.urllib.request.urlopen",
                   side_effect=OSError("offline")):
            with patch("scripts.discover_tortoise_diet_literature.time.sleep"):
                result = search(QUERIES[0], retries=1)
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["records"], [])

if __name__ == "__main__":
    unittest.main()
