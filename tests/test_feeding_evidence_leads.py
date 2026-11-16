import json
import tempfile
import unittest
from pathlib import Path
from scripts.stage_feeding_evidence_leads import process


def lead():
    return {"plant_scientific_name": "Taraxacum officinale", "source_url": "https://example.org/study",
            "source_type": "peer_reviewed", "source_title": "Feeding observations",
            "observed_at": "2026-11-16", "plant_part": "leaf",
            "tortoise_scientific_name": "Testudo graeca"}


class LeadTests(unittest.TestCase):
    def test_batch_dedupe_and_species_scope(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            a, b = root / "a.jsonl", root / "b.jsonl"
            a.write_text(json.dumps(lead()) + "\n")
            b.write_text(json.dumps(lead()) + "\n")
            result = process([a, b], root / "out.jsonl", root / "report.json")
            self.assertEqual(result, {"read": 2, "leads": 1, "duplicate": 1})
            row = json.loads((root / "out.jsonl").read_text())
            self.assertEqual(row["tortoise_scientific_name"], "Testudo graeca")
            self.assertIsNone(row["feeding_verdict"])

    def test_reject_verdict_without_partial_output(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            a = root / "a.jsonl"
            good = lead()
            bad = dict(good, safe=True)
            a.write_text(json.dumps(good) + "\n" + json.dumps(bad) + "\n")
            with self.assertRaises(ValueError):
                process([a], root / "out.jsonl", root / "report.json")
            self.assertFalse((root / "out.jsonl").exists())

    def test_missing_scope_not_inferred(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            a = root / "a.jsonl"
            item = lead()
            del item["plant_part"]
            del item["tortoise_scientific_name"]
            a.write_text(json.dumps(item) + "\n")
            process([a], root / "out.jsonl", root / "report.json")
            row = json.loads((root / "out.jsonl").read_text())
            self.assertIsNone(row["plant_part"])
            self.assertIsNone(row["tortoise_scientific_name"])


if __name__ == "__main__":
    unittest.main()
