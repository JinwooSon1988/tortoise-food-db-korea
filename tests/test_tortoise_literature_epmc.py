import json
import tempfile
import unittest
from pathlib import Path
from scripts.collect_tortoise_literature_epmc import QUERIES, collect, fetch_pages


class EuropePMCTests(unittest.TestCase):
    def test_parallel_results_deduplicate_and_preserve_unmatched_scope(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            def fetcher(query, size):
                return [{"source": "MED", "id": "123", "title": "Tortoise dietary study",
                         "doi": "10.1000/example", "pmcid": "PMC123456", "pubYear": "2024",
                         "abstractText": "Observed wild feeding; plant identification requires review."}]
            counts = collect(root / "leads.jsonl", root / "report.json", fetcher=fetcher)
            self.assertEqual(counts["raw_hits"], len(QUERIES))
            self.assertEqual(counts["unique_publications"], 1)
            self.assertEqual(counts["with_abstract"], 1)
            row = json.loads((root / "leads.jsonl").read_text())
            self.assertEqual(len(row["matching_queries"]), len(QUERIES))
            self.assertEqual(row["pmcid"], "PMC123456")
            self.assertIsNone(row["plant_scientific_name"])
            self.assertIsNone(row["feeding_verdict"])
            self.assertIn("plant identification requires review", row["abstract_text"])


    def test_cursor_pagination_collects_all_pages(self):
        from io import BytesIO
        from urllib.parse import parse_qs, urlparse
        calls = []
        class Response(BytesIO):
            def __enter__(self):
                return self
            def __exit__(self, *args):
                self.close()
        def opener(request, timeout):
            cursor = parse_qs(urlparse(request.full_url).query)["cursorMark"][0]
            calls.append(cursor)
            payload = {"resultList": {"result": [{"id": cursor}] * (2 if cursor == "*" else 1)},
                       "nextCursorMark": "second" if cursor == "*" else "third"}
            return Response(json.dumps(payload).encode())
        rows = fetch_pages("tortoise diet", 2, max_pages=3, opener=opener)
        self.assertEqual(len(rows), 3)
        self.assertEqual(calls, ["*", "second"])

    def test_cursor_pagination_rejects_repeated_cursor(self):
        from io import BytesIO
        class Response(BytesIO):
            def __enter__(self):
                return self
            def __exit__(self, *args):
                self.close()
        def opener(request, timeout):
            return Response(json.dumps({"resultList": {"result": [{"id": "x"}]},
                                        "nextCursorMark": "*"}).encode())
        rows = fetch_pages("tortoise", 1, max_pages=3, opener=opener)
        self.assertEqual(len(rows), 1)

    def test_failed_query_does_not_publish_partial_output(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            def fetcher(query, size):
                raise RuntimeError("upstream unavailable")
            with self.assertRaises(RuntimeError):
                collect(root / "leads.jsonl", root / "report.json", fetcher=fetcher)
            self.assertFalse((root / "leads.jsonl").exists())
            self.assertFalse((root / "report.json").exists())

    def test_conflicting_metadata_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            def fetcher(query, size):
                return [{"source": "MED", "id": "123", "title": query}]
            with self.assertRaisesRegex(ValueError, "conflicting publication metadata"):
                collect(root / "leads.jsonl", root / "report.json", fetcher=fetcher)
            self.assertFalse((root / "leads.jsonl").exists())


if __name__ == "__main__":
    unittest.main()
