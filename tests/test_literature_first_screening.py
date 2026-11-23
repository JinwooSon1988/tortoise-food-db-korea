import unittest
from scripts.screen_literature_first_titles import screen


class LiteratureScreenTests(unittest.TestCase):
    def test_conservative_multilingual_titles(self):
        def work(title, i):
            return {"title": title, "openalex_id": f"https://openalex.org/W{i}",
                    "status": "literature_lead_unreviewed", "feeding_confirmed": False}
        report = screen({"scope": "literature_first_unreviewed_not_feeding_evidence",
                         "works": [work("Testudo graeca diet and vegetation", 1),
                                   work("Alimentación de tortuga mora", 2),
                                   work("Unrelated plant nutrition", 3)]})
        self.assertEqual(report["title_candidates"], 2)
        self.assertEqual(report["feeding_verdicts_confirmed"], 0)
        self.assertTrue(all(x["feeding_confirmed"] is False for x in report["candidates"]))

    def test_rejects_unsafe_promotion(self):
        with self.assertRaises(ValueError):
            screen({"scope": "literature_first_unreviewed_not_feeding_evidence",
                    "works": [{"status": "literature_lead_unreviewed", "feeding_confirmed": True}]})
        with self.assertRaises(ValueError):
            screen({"scope": "other", "works": []})


if __name__ == "__main__":
    unittest.main()
