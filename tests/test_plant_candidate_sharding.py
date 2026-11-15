import json
import tempfile
import unittest
from pathlib import Path
from scripts.shard_plant_candidates import shard


class ShardingTests(unittest.TestCase):
    def test_25000_rows_stable_32_queues(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "candidates.jsonl"
            with source.open("w", encoding="utf-8") as stream:
                for i in range(25000):
                    stream.write(json.dumps({"candidate_id": f"src:{i}",
                                             "feed_review_status": "identity_only"}) + "\n")
            report = shard(source, root / "first", 32)
            self.assertEqual(report["total"], 25000)
            self.assertEqual(len(report["counts"]), 32)
            self.assertTrue(all(count > 0 for count in report["counts"]))
            report2 = shard(source, root / "second", 32)
            self.assertEqual(report["counts"], report2["counts"])
            for i in range(32):
                name = f"queue-{i:03d}.jsonl"
                self.assertEqual((root / "first" / name).read_bytes(),
                                 (root / "second" / name).read_bytes())

    def test_invalid_row_removes_partial_queues(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "in.jsonl"
            source.write_text('{"candidate_id":"ok","feed_review_status":"identity_only"}\n'
                              '{"candidate_id":"unsafe","feed_review_status":"assessed"}\n', encoding="utf-8")
            output = root / "queues"
            with self.assertRaises(ValueError):
                shard(source, output, 4)
            self.assertEqual(list(output.glob("queue-*.jsonl")), [])


if __name__ == "__main__":
    unittest.main()
