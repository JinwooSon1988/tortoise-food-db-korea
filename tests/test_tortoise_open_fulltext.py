import json
import tempfile
import unittest
from pathlib import Path
from scripts.collect_tortoise_open_fulltext import enrich, extract_structured_body, retrieve


class OpenFulltextTests(unittest.TestCase):



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
