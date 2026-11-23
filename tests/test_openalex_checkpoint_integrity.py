"""Checkpoint recovery must never silently lose successful literature searches."""
import json
import tempfile
import unittest
from pathlib import Path

from scripts.research_bulk_leads import load_completed_checkpoint, select_taxa


class OpenAlexCheckpointTests(unittest.TestCase):
    def test_offset_windows_remain_disjoint_with_completed_rows(self):
        source = [{'name': f'Plant {i}'} for i in range(12)]
        first = select_taxa(iter(source), {'plant 2'}, 0, 5)
        second = select_taxa(iter(source), {'plant 7'}, 5, 5)
        self.assertEqual([x['name'] for x in first], ['Plant 0', 'Plant 1', 'Plant 3', 'Plant 4'])
        self.assertEqual([x['name'] for x in second], ['Plant 5', 'Plant 6', 'Plant 8', 'Plant 9'])
        self.assertFalse({x['name'] for x in first} & {x['name'] for x in second})


    def test_completed_only_and_retryable(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "leads.jsonl"
            with path.open("w", encoding="utf-8") as stream:
                stream.write(json.dumps({"name": "Plantago major", "status": "searched"}) + "\n")
                stream.write(json.dumps({"name": "Abies alba", "status": "retry_needed"}) + "\n")
            self.assertEqual(load_completed_checkpoint(path), {"plantago major"})

    def test_interrupted_final_write_is_truncated_before_append(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "leads.jsonl"
            valid = (json.dumps({"name": "Plantago major", "status": "searched"}) + "\n").encode()
            path.write_bytes(valid + b'{"name":"Abies alba","status":"sear')
            self.assertEqual(load_completed_checkpoint(path), {"plantago major"})
            self.assertEqual(path.read_bytes(), valid)

    def test_corrupt_complete_line_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "leads.jsonl"
            path.write_bytes(b'{"name": "Plantago major", "status": "searched"}\nnot-json\n')
            with self.assertRaisesRegex(ValueError, "corrupt completed checkpoint line 2"):
                load_completed_checkpoint(path)

    def test_valid_final_row_without_newline_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "leads.jsonl"
            row = json.dumps({"name": "Plantago major", "status": "searched"}).encode()
            path.write_bytes(row)
            self.assertEqual(load_completed_checkpoint(path), {"plantago major"})
            self.assertEqual(path.read_bytes(), row + b'\n')
            self.assertEqual(load_completed_checkpoint(path), {"plantago major"})

    def test_invalid_final_tail_still_truncates(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "leads.jsonl"
            path.write_bytes(b'{"name":"Plantago major","status":"sear')
            self.assertEqual(load_completed_checkpoint(path), set())
            self.assertEqual(path.read_bytes(), b'')

    def test_missing_name_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "leads.jsonl"
            path.write_text('{"status":"searched"}\n', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "missing checkpoint taxon"):
                load_completed_checkpoint(path)


if __name__ == "__main__":
    unittest.main()
