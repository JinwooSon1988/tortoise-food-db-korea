import unittest
from scripts.dedup_abstract_review_queue import group_mentions


class ReviewQueueDedupTests(unittest.TestCase):
    def test_merges_same_work_and_candidate_without_claiming_safety(self):
        rows = [
            {"openalex_id": "https://openalex.org/W1", "candidate_binomial": "Erodium cicutarium",
             "context": "diet", "feeding_keyword_nearby": "True", "negation_keyword_nearby": "False"},
            {"openalex_id": "https://openalex.org/W1", "candidate_binomial": "Erodium cicutarium",
             "context": "not eaten", "feeding_keyword_nearby": "True", "negation_keyword_nearby": "True"},
            {"openalex_id": "https://openalex.org/W2", "candidate_binomial": "Erodium cicutarium",
             "context": "diet", "feeding_keyword_nearby": "False", "negation_keyword_nearby": "False"},
        ]
        result = group_mentions(rows)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["mention_count"], 2)
        self.assertEqual(result[0]["feeding_keyword_windows"], 2)
        self.assertEqual(result[0]["negation_keyword_windows"], 1)
        self.assertTrue(all(x["safety_status"] == "not_assessed" for x in result))

    def test_skips_invalid_identifier(self):
        self.assertEqual(group_mentions([{"openalex_id": "invalid", "candidate_binomial": "Plant name"}]), [])


if __name__ == "__main__":
    unittest.main()
