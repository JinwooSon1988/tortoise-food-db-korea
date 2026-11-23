import unittest
from scripts.prioritize_tortoise_literature import prioritize


class PrioritizeLiteratureTests(unittest.TestCase):
    def test_deduplicates_and_keeps_unverified(self):
        rows = [
            {"openalex_id": "https://openalex.org/W1", "title": "Testudo graeca diet and food plants"},
            {"openalex_id": "https://openalex.org/W1", "title": "duplicate"},
            {"openalex_id": "https://openalex.org/W2", "title": "Unrelated publication"},
        ]
        ranked = prioritize(rows)
        self.assertEqual(len(ranked), 2)
        self.assertEqual(ranked[0]["triage_bucket"], "high_title_priority")
        self.assertTrue(all(x["feeding_verdict"] == "unverified" for x in ranked))
        self.assertEqual(ranked[1]["triage_bucket"], "background_or_low_relevance")

    def test_empty_ids_not_accepted(self):
        self.assertEqual(prioritize([{"openalex_id": "", "title": "Testudo diet"}]), [])


if __name__ == "__main__":
    unittest.main()
