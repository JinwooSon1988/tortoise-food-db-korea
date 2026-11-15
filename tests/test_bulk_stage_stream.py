import json
import tempfile
import unittest
from pathlib import Path
from scripts.stage_plant_bulk_stream import stage


class BulkStageTests(unittest.TestCase):
    def test_large_stream_deduplicates_and_stays_identity_only(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            src, out, report = (root / name for name in ("in.jsonl", "out.jsonl", "report.json"))
            with src.open("w", encoding="utf-8") as f:
                for i in range(25000):
                    row = {"scientific_name": f"Plantus example{i}", "source_id": "WCVP",
                           "source_record_id": str(i), "source_url": "https://example.org/taxa/" + str(i),
                           "observed_at": "2026-11-15"}
                    f.write(json.dumps(row) + "\n")
                f.write(json.dumps(row) + "\n")
            result = stage(src, out, report)
            self.assertTrue(result["passed"])
            self.assertEqual(result["counts"]["staged"], 25000)
            self.assertEqual(result["counts"]["duplicates"], 1)
            lines = out.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 25000)
            self.assertEqual(json.loads(lines[0])["feed_review_status"], "identity_only")
            self.assertNotIn("verdict", json.loads(lines[0]))

    def test_invalid_input_never_replaces_previous_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            src, out, report = (root / name for name in ("in.jsonl", "out.jsonl", "report.json"))
            out.write_text("existing", encoding="utf-8")
            src.write_text('{"scientific_name":"Test","source_id":"X","source_url":"file:///unsafe","observed_at":"2026-11-15"}\n', encoding="utf-8")
            result = stage(src, out, report)
            self.assertFalse(result["passed"])
            self.assertEqual(out.read_text(encoding="utf-8"), "existing")
            self.assertEqual(result["counts"]["rejected"], 1)


if __name__ == "__main__":
    unittest.main()
