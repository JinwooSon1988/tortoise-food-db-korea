import unittest

from scripts.extract_abstract_review_contexts import extract


class AbstractContextTests(unittest.TestCase):
    def test_extracts_context_but_never_confirms_feeding(self):
        rows = extract([{"openalex_id": "https://openalex.org/W123",
                         "abstract": "Gopherus agassizii consumed Erodium cicutarium during spring."}])
        self.assertEqual(len(rows), 2)
        plant = next(x for x in rows if x["candidate_binomial"] == "Erodium cicutarium")
        self.assertTrue(plant["feeding_keyword_nearby"])
        self.assertEqual(plant["taxonomic_identity"], "unverified")
        self.assertEqual(plant["feeding_event"], "unverified")
        self.assertEqual(plant["safety_verdict"], "not_assessed")

    def test_negative_context_is_not_safe(self):
        rows = extract([{"openalex_id": "https://openalex.org/W2",
                         "abstract": "Tortoises did not eat Bromus rubens."}])
        self.assertTrue(all(x["safety_verdict"] == "not_assessed" for x in rows))
        self.assertTrue(any(x["negation_keyword_nearby"] for x in rows))

    def test_invalid_and_missing_abstract_skipped(self):
        self.assertEqual(extract([{"openalex_id": "invalid", "abstract": "Erodium cicutarium"},
                                  {"openalex_id": "https://openalex.org/W3", "abstract": None}]), [])

    def test_reject_short_window(self):
        with self.assertRaises(ValueError):
            extract([], context_chars=20)


if __name__ == "__main__":
    unittest.main()
