import json
import tempfile
import unittest
from pathlib import Path
from scripts.collect_tortoise_open_fulltext import enrich


class OpenFulltextTests(unittest.TestCase):
    def test_parallel_review_only_and_missing_fulltext(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rows = [
                {"source_database": "PMC", "source_record_id": "PMC123",
                 "source_url": "https://europepmc.org/article/PMC/PMC123", "title": "Diet paper"},
                {"source_database": "PMC", "source_record_id": "PMC456",
                 "source_url": "https://europepmc.org/article/PMC/PMC456", "title": "Other paper"},
                {"source_database": "MED", "source_record_id": "100",
                 "source_url": "https://europepmc.org/article/MED/100"}]
            (root / "input.jsonl").write_text("".join(json.dumps(x) + "\n" for x in rows))
            result = enrich(root / "input.jsonl", root / "out.jsonl", root / "report.json",
                            fetcher=lambda pmcid: "Wild tortoise consumed leaves." if pmcid == "PMC123" else None)
            self.assertEqual(result["pmc_candidates"], 2)
            self.assertEqual(result["fulltexts_retrieved"], 1)
            output = json.loads((root / "out.jsonl").read_text())
            self.assertIsNone(output["feeding_verdict"])
            self.assertEqual(output["review_status"], "unverified_fulltext_for_manual_review")


if __name__ == "__main__":
    unittest.main()
