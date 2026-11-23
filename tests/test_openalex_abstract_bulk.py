import unittest
from scripts.enrich_openalex_abstracts import decode_abstract, enrich


class AbstractBulkTests(unittest.TestCase):
    def test_inverted_index_and_dedup(self):
        calls = []
        def fetch(url):
            calls.append(url)
            return {"results": [{"id": "https://openalex.org/W1",
                                 "abstract_inverted_index": {"Tortoise": [0], "diet": [1]}}]}
        result = enrich([{"openalex_id": "https://openalex.org/W1"},
                         {"openalex_id": "https://openalex.org/W1"}],
                        fetch, sleep=lambda _: None)
        self.assertEqual(result["input_unique_ids"], 1)
        self.assertEqual(result["abstracts_available"], 1)
        self.assertEqual(result["records"][0]["abstract"], "Tortoise diet")
        self.assertFalse(result["records"][0]["feeding_confirmed"])
        self.assertEqual(result["feeding_verdicts_confirmed"], 0)
        self.assertEqual(len(calls), 1)

    def test_missing_abstract_and_bad_index(self):
        self.assertIsNone(decode_abstract(None))
        with self.assertRaises(ValueError):
            decode_abstract({"A": [0], "B": [0]})
        result = enrich([], lambda _: self.fail("should not fetch"))
        self.assertEqual(result["input_unique_ids"], 0)


if __name__ == "__main__":
    unittest.main()
