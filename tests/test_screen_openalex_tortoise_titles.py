import json
import tempfile
import unittest
from pathlib import Path
from scripts.screen_openalex_tortoise_titles import screen


class TitleScreenTests(unittest.TestCase):
    def test_dedup_and_unrelated_tortoise_tick_not_feeding(self):
        rows = [
            {"name": "Abies alba", "status": "searched", "hits": [
                {"openalex_id": "W1", "title": "Tortoise tick control", "status": "literature_lead_unreviewed"},
                {"openalex_id": "W2", "title": "Eagle diet", "status": "literature_lead_unreviewed"}]},
            {"name": "Abies amabilis", "status": "searched", "hits": [
                {"openalex_id": "W1", "title": "Tortoise tick control", "status": "literature_lead_unreviewed"}]}
        ]
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "leads.jsonl"
            path.write_text("".join(json.dumps(r) + "\n" for r in rows))
            result = screen(path)
        self.assertEqual(result["unique_works"], 2)
        self.assertEqual(result["tortoise_title_candidates"], 1)
        self.assertEqual(result["tortoise_and_diet_title_candidates"], 0)
        self.assertEqual(result["feeding_verdicts_confirmed"], 0)
        self.assertEqual(len(result["candidates_for_manual_abstract_review"][0]["plant_names"]), 2)

    def test_rejects_verified_hit_status(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "leads.jsonl"
            path.write_text(json.dumps({"name": "Abies alba", "status": "searched",
                                        "hits": [{"openalex_id": "W1", "status": "feeding_verified"}]}) + "\n")
            with self.assertRaisesRegex(ValueError, "unreviewed"):
                screen(path)


if __name__ == "__main__":
    unittest.main()
