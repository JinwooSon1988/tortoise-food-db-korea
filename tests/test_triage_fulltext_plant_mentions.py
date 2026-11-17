import json
import tempfile
import unittest
from pathlib import Path
from scripts.triage_fulltext_plant_mentions import triage


class TriageFulltextPlantMentionsTests(unittest.TestCase):
    def test_batch_prioritization_keeps_unverified_and_flags_negation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            base = {"source_database": "MED", "source_record_id": "100",
                    "source_url": "https://europepmc.org/article/MED/100",
                    "review_status": "unverified_fulltext_mention",
                    "feeding_verdict": None}
            records = [
                {**base, "plant_scientific_name": "Plantago major",
                 "mention_context": "Testudo graeca consumed Plantago major leaves."},
                {**base, "plant_scientific_name": "Taraxacum officinale",
                 "mention_context": "No tortoise fed Taraxacum officinale."},
            ]
            source = root / "source.jsonl"
            source.write_text("".join(json.dumps(row) + "\n" for row in records))
            self.assertEqual(triage(source, root / "output.jsonl", root / "report.json"), 2)
            rows = [json.loads(line) for line in (root / "output.jsonl").read_text().splitlines()]
            self.assertEqual(rows[0]["plant_scientific_name"], "Plantago major")
            self.assertTrue(rows[1]["triage_signals"]["negation_or_hazard_language"])
            self.assertTrue(all(row["feeding_verdict"] is None for row in rows))
            self.assertTrue(all(row["review_status"] == "unverified_fulltext_mention" for row in rows))
            report = json.loads((root / "report.json").read_text())
            self.assertEqual(report["candidates"], 2)
            self.assertEqual(report["with_both"], 2)

    def test_rejects_promoted_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.jsonl"
            source.write_text(json.dumps({"source_database": "PMC", "source_record_id": "PMC1",
                "plant_scientific_name": "Plantago major", "mention_context": "feed",
                "review_status": "confirmed", "feeding_verdict": "safe"}) + "\n")
            with self.assertRaises(ValueError):
                triage(source, root / "out.jsonl", root / "report.json")
            self.assertFalse((root / "out.jsonl").exists())


if __name__ == "__main__":
    unittest.main()
