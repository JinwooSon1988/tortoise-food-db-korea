import unittest
from unittest.mock import patch
from scripts.discover_tortoise_diet_literature import combine, search, QUERIES, uniform_provider_outage, title_signal, crossref_fallback, merge_provider_results, fallback_failed_queries

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

    def test_fallback_queries_only_failed_primary_searches(self):
        primary = [
            {"query": "ok", "status": "ok", "records": [{"doi": "10.1/ok"}]},
            {"query": "failed", "status": "error", "http_status": 503, "records": []}]
        replacement = [{"query": "failed", "status": "ok", "provider": "crossref",
                        "records": [{"doi": "10.1/recovered"}]}]
        with patch("scripts.discover_tortoise_diet_literature.crossref_fallback",
                   return_value=replacement) as fetch:
            result = fallback_failed_queries(primary, workers=4)
        fetch.assert_called_once_with(["failed"], workers=4)
        self.assertEqual(result[0]["records"][0]["doi"], "10.1/ok")
        self.assertEqual(result[1]["records"][0]["doi"], "10.1/recovered")
        self.assertEqual(len(result[1]["provider_attempts"]), 2)
        with patch("scripts.discover_tortoise_diet_literature.crossref_fallback") as fetch:
            self.assertEqual(fallback_failed_queries(primary[:1]), primary[:1])
            fetch.assert_not_called()

    def test_provider_merge_preserves_success_and_both_diagnostics(self):
        primary = [{"query": "a", "status": "ok", "records": [{"doi": "10.1/a"}]},
                   {"query": "b", "status": "error", "http_status": 503, "records": []}]
        fallback = [{"query": "a", "status": "error", "http_status": 429, "records": []},
                    {"query": "b", "status": "ok", "provider": "crossref",
                     "records": [{"doi": "10.1/b"}]}]
        result = merge_provider_results(primary, fallback)
        self.assertEqual(result[0]["records"][0]["doi"], "10.1/a")
        self.assertEqual(result[1]["records"][0]["doi"], "10.1/b")
        self.assertEqual(len(result[1]["provider_attempts"]), 2)
        with self.assertRaises(ValueError):
            merge_provider_results(primary, fallback[::-1])

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

    def test_crossref_429_retry_recovers_without_verifying_feeding(self):
        import io
        import json
        import urllib.error
        class Response(io.BytesIO):
            def __enter__(self):
                return self
            def __exit__(self, *args):
                self.close()
        payload = {"message": {"items": [
            {"DOI": "10.1000/diet", "title": ["Testudo graeca diet composition"]}]}}
        throttled = urllib.error.HTTPError(
            "https://api.crossref.org/works", 429, "rate limited",
            {"Retry-After": "0.5"}, None)
        with patch("scripts.discover_tortoise_diet_literature.urllib.request.urlopen",
                   side_effect=[throttled, Response(json.dumps(payload).encode())]):
            with patch("scripts.discover_tortoise_diet_literature.time.sleep") as sleep:
                rows = crossref_fallback(["Testudo diet"], workers=1)
        self.assertEqual(rows[0]["status"], "ok")
        self.assertEqual(rows[0]["attempts"], 2)
        self.assertEqual(len(rows[0]["records"]), 1)
        sleep.assert_called_once()

    def test_html_title_and_crossref_year_provenance(self):
        import io
        import json
        class Response(io.BytesIO):
            def __enter__(self):
                return self
            def __exit__(self, *args):
                self.close()
        payload = {"message": {"items": [{
            "DOI": "10.1000/html", "title": ["Foraging of <i>Testudo graeca</i>"],
            "published": {"date-parts": [[2023, 4]]},
            "container-title": ["Ecology Journal"]}]}}
        with patch("scripts.discover_tortoise_diet_literature.urllib.request.urlopen",
                   return_value=Response(json.dumps(payload).encode())):
            result = combine(crossref_fallback(["Testudo diet"], workers=1))
        self.assertEqual(result["unique_sources"], 1)
        self.assertEqual(result["records"][0]["year"], 2023)
        self.assertEqual(result["records"][0]["metadata_provider"], "crossref")

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
