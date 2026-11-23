import unittest
from scripts.consolidate_species_review_queue import consolidate


class SpeciesReviewTests(unittest.TestCase):
    def test_same_paper_repeated_not_independent(self):
        row = {"candidate_binomial": "Erodium cicutarium",
               "openalex_id": "https://openalex.org/W1",
               "abstract_context_bucket": "experimental_diet_or_nutrition_abstract",
               "sample_context": "A feeding experiment was conducted."}
        result = consolidate([row, row])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["unique_papers"], 1)
        self.assertEqual(result[0]["unique_paper_plant_pairs"], 1)
        self.assertEqual(result[0]["safety_verdict"], "not_assessed")
        self.assertEqual(result[0]["full_text_checked"], "no")

    def test_priority_and_invalid_rows(self):
        rows = [{"candidate_binomial": "Lactuca virosa", "openalex_id": "https://openalex.org/W2",
                 "abstract_context_bucket": "habitat_vegetation_or_unrelated_context"},
                {"candidate_binomial": "Lactuca virosa", "openalex_id": "https://openalex.org/W3",
                 "abstract_context_bucket": "clinical_adverse_event_abstract"},
                {"candidate_binomial": "Barn owl", "openalex_id": "invalid",
                 "abstract_context_bucket": "clinical_adverse_event_abstract"}]
        result = consolidate(rows)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["review_priority"], 1)
        self.assertEqual(result[0]["unique_papers"], 2)
        self.assertEqual(result[0]["feeding_confirmed"], "no_full_text_verification")


if __name__ == "__main__":
    unittest.main()
