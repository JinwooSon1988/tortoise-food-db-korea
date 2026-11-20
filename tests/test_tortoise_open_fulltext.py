import json
import tempfile
import unittest
from pathlib import Path
from scripts.collect_tortoise_open_fulltext import enrich, extract_structured_body, retrieve


class OpenFulltextTests(unittest.TestCase):



    def test_transient_http_failure_retries_but_404_does_not(self):
        from io import BytesIO
        from urllib.error import HTTPError
        xml = b"<article><body><p>Plantago major.</p></body></article>"
        calls = []
        delays = []
        def opener(req, timeout):
            calls.append(timeout)
            if len(calls) == 1:
                raise HTTPError(req.full_url, 503, "busy", {}, None)
            return BytesIO(xml)
        self.assertIn("Plantago major.", retrieve("PMC123", opener=opener,
                                                 sleeper=delays.append))
        self.assertEqual(len(calls), 2)
        self.assertEqual(delays, [0.5])
        missing_calls = []
        def missing(req, timeout):
            missing_calls.append(1)
            raise HTTPError(req.full_url, 404, "not found", {}, None)
        self.assertIsNone(retrieve("PMC123", opener=missing,
                                   sleeper=lambda delay: self.fail("unexpected retry")))
        self.assertEqual(len(missing_calls), 1)

    def test_persistent_transient_timeout_is_bounded(self):
        calls = []
        delays = []
        def timeout(request, timeout):
            calls.append(timeout)
            raise TimeoutError("upstream timed out")
        self.assertIsNone(retrieve("PMC123", opener=timeout, sleeper=delays.append))
        self.assertEqual(len(calls), 3)
        self.assertEqual(delays, [0.5, 1.0])

    def test_pmc_request_concurrency_is_bounded(self):
        import concurrent.futures
        import threading
        from io import BytesIO
        from scripts.collect_tortoise_open_fulltext import PMC_REQUEST_SLOTS
        active = 0
        peak = 0
        lock = threading.Lock()
        release = threading.Event()
        xml = b"<article><body><p>Plantago major.</p></body></article>"
        def opener(request, timeout):
            nonlocal active, peak
            with lock:
                active += 1
                peak = max(peak, active)
            release.wait(0.15)
            with lock:
                active -= 1
            return BytesIO(xml)
        with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
            futures = [pool.submit(retrieve, f"PMC{i+1}", opener=opener) for i in range(12)]
            results = [future.result(timeout=10) for future in futures]
        self.assertTrue(all("Plantago major." in item for item in results))
        self.assertLessEqual(peak, 8)
        self.assertGreaterEqual(peak, 1)

    def test_namespaced_jats_body_is_extracted(self):
        from io import BytesIO
        xml = (b'<article xmlns="http://jats.nlm.nih.gov">'
               b'<body><sec><p>Testudo graeca consumed Plantago major.</p>'
               b'</sec></body></article>')
        class Response(BytesIO):
            def __enter__(self):
                return self
            def __exit__(self, *args):
                self.close()
        result = retrieve("PMC123456", opener=lambda request, timeout: Response(xml))
        self.assertIn("Testudo graeca consumed Plantago major.", result)

    def test_jats_paragraphs_and_table_rows_remain_separate(self):
        import xml.etree.ElementTree as ET
        body = ET.fromstring(
            "<body><sec><title>Diet</title><p>Testudo graeca ate "
            "<italic>Plantago major</italic>.</p>"
            "<table-wrap><table><tbody><tr><td>Plantago</td><td>major</td></tr>"
            "<tr><td>Taraxacum officinale</td><td>leaf</td></tr>"
            "</tbody></table></table-wrap></sec></body>"
        )
        text = extract_structured_body(body)
        self.assertIn("Testudo graeca ate Plantago major.", text)
        self.assertIn("Plantago | major", text)
        self.assertNotIn("Plantago major\\nTaraxacum", text)
        self.assertIn("Taraxacum officinale", text)
        self.assertGreater(len(text.splitlines()), 2)

    def test_same_pmcid_fetched_once_but_both_publications_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rows = [
                {"source_database": "MED", "source_record_id": "123", "pmcid": "PMC999",
                 "source_url": "https://europepmc.org/article/MED/123"},
                {"source_database": "PMC", "source_record_id": "PMC999",
                 "source_url": "https://europepmc.org/article/PMC/PMC999"},
            ]
            (root / "input.jsonl").write_text("".join(json.dumps(x) + "\n" for x in rows))
            calls = []
            def fetcher(pmcid):
                calls.append(pmcid)
                return "Testudo graeca consumed Plantago major."
            counts = enrich(root / "input.jsonl", root / "out.jsonl", root / "report.json",
                            fetcher=fetcher)
            self.assertEqual(calls, ["PMC999"])
            self.assertEqual(counts["pmc_candidates"], 2)
            self.assertEqual(counts["unique_pmc_requests"], 1)
            self.assertEqual(counts["duplicate_pmc_requests_avoided"], 1)
            output = [json.loads(line) for line in (root / "out.jsonl").read_text().splitlines()]
            self.assertEqual(len(output), 2)
            self.assertEqual({r["source_database"] for r in output}, {"MED", "PMC"})
            self.assertTrue(all(r["feeding_verdict"] is None for r in output))

    def test_large_parallel_fulltext_spool_preserves_all_records(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rows = [
                {"source_database": "PMC", "source_record_id": f"PMC{i}",
                 "source_url": f"https://europepmc.org/article/PMC/PMC{i}",
                 "title": f"Study {i}"} for i in range(1, 121)
            ]
            (root / "input.jsonl").write_text(
                "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
            counts = enrich(root / "input.jsonl", root / "out.jsonl",
                            root / "report.json", workers=12,
                            fetcher=lambda pmcid: "Plantago major " * 2000)
            self.assertEqual(counts["fulltexts_retrieved"], 120)
            self.assertEqual(counts["unique_pmc_requests"], 120)
            output = [json.loads(line) for line in
                      (root / "out.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(output), 120)
            self.assertEqual(output[0]["source_record_id"], "PMC1")
            self.assertEqual(output[-1]["source_record_id"], "PMC120")
            self.assertTrue(all(item["feeding_verdict"] is None for item in output))

    def test_parallel_review_only_and_missing_fulltext(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rows = [
                {"source_database": "PMC", "source_record_id": "PMC123",
                 "source_url": "https://europepmc.org/article/PMC/PMC123", "title": "Diet paper"},
                {"source_database": "PMC", "source_record_id": "PMC456",
                 "source_url": "https://europepmc.org/article/PMC/PMC456", "title": "Other paper"},
                {"source_database": "MED", "source_record_id": "100", "pmcid": "PMC789",
                 "source_url": "https://europepmc.org/article/MED/100"}]
            (root / "input.jsonl").write_text("".join(json.dumps(x) + "\n" for x in rows))
            result = enrich(root / "input.jsonl", root / "out.jsonl", root / "report.json",
                            fetcher=lambda pmcid: "Wild tortoise consumed leaves." if pmcid == "PMC123" else None)
            self.assertEqual(result["pmc_candidates"], 3)
            self.assertEqual(result["fulltexts_retrieved"], 1)
            self.assertEqual(result["unavailable_fulltext"], 2)
            output = json.loads((root / "out.jsonl").read_text())
            self.assertIsNone(output["feeding_verdict"])
            self.assertEqual(output["review_status"], "unverified_fulltext_for_manual_review")


if __name__ == "__main__":
    unittest.main()
