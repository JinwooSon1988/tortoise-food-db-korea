import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.discover_research_sources_epmc import main


class DiscoveryCircuitBreakerTests(unittest.TestCase):
    def test_uniform_503_stops_after_three_probes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            records = [
                {"source_url": f"https://doi.org/10.1234/{i}",
                 "title": f"Example {i}", "taxon_associations": []}
                for i in range(12)
            ]
            queue = root / "queue.json"
            output = root / "out.json"
            queue.write_text(json.dumps({"records": records}), encoding="utf-8")
            def unavailable(record):
                return {
                    "source_url": record["source_url"],
                    "queue_title": record["title"],
                    "candidate_taxon_count": 0,
                    "feeding_safety_status": "unassessed",
                    "plant_associations_verified": 0,
                    "discovery_status": "lookup_error",
                    "error_type": "HTTPError",
                    "http_status": 503,
                    "attempts": 3
                }
            with patch("scripts.discover_research_sources_epmc.lookup", side_effect=unavailable) as lookup, \
                 patch.object(sys, "argv", ["discover", "--queue", str(queue),
                                            "--out", str(output), "--workers", "12"]):
                main()
            data = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(lookup.call_count, 3)
            self.assertEqual(data["total_sources"], 12)
            self.assertEqual(data["status_counts"]["lookup_error"], 12)
            self.assertEqual(sum(r["attempts"] for r in data["records"]), 9)
            self.assertEqual(sum(r["error_type"] == "circuit_open_after_uniform_http_failure"
                                 for r in data["records"]), 9)
            self.assertTrue(all(r["feeding_safety_status"] == "unassessed"
                                for r in data["records"]))


if __name__ == "__main__":
    unittest.main()
