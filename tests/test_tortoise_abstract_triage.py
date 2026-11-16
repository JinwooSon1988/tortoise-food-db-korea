import json
import tempfile
import unittest
from pathlib import Path
from scripts.triage_tortoise_abstracts import screen, contextual_excerpts


class AbstractTriageTests(unittest.TestCase):
    def test_screening_does_not_infer_verdict(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            lead = {"source_record_id": "1", "source_database": "MED",
                    "source_url": "https://europepmc.org/article/MED/1",
                    "review_status": "unmatched_literature_lead",
                    "abstract_text": "Wild tortoises were observed feeding on Taraxacum officinale leaves."}
            (root / "in.jsonl").write_text(json.dumps(lead) + "\n")
            totals = screen(root / "in.jsonl", root / "out.jsonl", root / "report.json")
            self.assertEqual(totals["abstract_review"], 1)
            row = json.loads((root / "out.jsonl").read_text())
            self.assertIn("Taraxacum officinale", row["unverified_binomial_strings"])
            self.assertIsNone(row["feeding_verdict"])
            self.assertEqual(len(row["plant_diet_context_excerpts"]), 1)
            self.assertIn("Taraxacum officinale", row["plant_diet_context_excerpts"][0])
            self.assertEqual(row["review_status"], "manual_validation_required")

    def test_excerpts_do_not_merge_unrelated_sentences(self):
        abstract = "Plant diversity was measured. Tortoises were feeding. No diet data."
        self.assertEqual(contextual_excerpts(abstract), [])

    def test_bad_input_fails(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "in.jsonl").write_text(json.dumps({"review_status": "published"}) + "\n")
            with self.assertRaises(ValueError):
                screen(root / "in.jsonl", root / "out.jsonl", root / "report.json")
            self.assertFalse((root / "out.jsonl").exists())


if __name__ == "__main__":
    unittest.main()
