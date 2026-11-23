import unittest
from scripts.discover_tortoise_diet_literature import QUERIES, build_url, collect


class LiteratureFirstTests(unittest.TestCase):
    def test_fixed_window_deduplicates_and_never_confirms_feeding(self):
        urls = []
        def fetch(url):
            urls.append(url)
            return {"results": [{"id": "https://openalex.org/W123", "doi": None,
                                  "title": "Example paper", "publication_year": 2024,
                                  "primary_location": {"landing_page_url": "https://example.org/paper"}}]}
        delays = []
        result = collect(fetch, delays.append, start=1, limit=3)
        self.assertEqual(result["queries_completed"], 3)
        self.assertEqual(result["unique_works"], 1)
        self.assertEqual(result["feeding_verdicts_confirmed"], 0)
        self.assertEqual(len(result["works"][0]["query_matches"]), 3)
        self.assertFalse(result["works"][0]["feeding_confirmed"])
        self.assertEqual(delays, [3.0, 3.0])
        self.assertEqual(len(urls), 3)
        self.assertEqual(result["queries"][0]["index"], 1)

    def test_invalid_bounds_and_response_fail_closed(self):
        with self.assertRaises(ValueError):
            collect(lambda _: {}, lambda _: None, interval=0)
        with self.assertRaises(ValueError):
            collect(lambda _: {}, lambda _: None, limit=1)

    def test_queries_include_species_and_topic(self):
        self.assertIn("Testudo", build_url(*QUERIES[0]))
        self.assertIn("search=", build_url(*QUERIES[0]))


if __name__ == "__main__":
    unittest.main()
