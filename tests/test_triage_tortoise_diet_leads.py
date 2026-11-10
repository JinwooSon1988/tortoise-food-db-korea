import unittest
from scripts.triage_tortoise_diet_leads import triage, normalize_title

class TortoiseDietLeadTriageTests(unittest.TestCase):
    def test_title_normalization(self):
        self.assertEqual(normalize_title("Testudo <i>graeca</i>  diet &amp; ecology"), "Testudo graeca diet & ecology")

    def test_html_entities_and_adjacent_tags_preserve_word_boundaries(self):
        self.assertEqual(
            normalize_title("The tortoise<i>Kinixys spekii</i>in relation to diet"),
            "The tortoise Kinixys spekii in relation to diet")
        self.assertEqual(
            normalize_title("Testudo &lt;i&gt;graeca&lt;/i&gt; diet"),
            "Testudo graeca diet")

    def test_deduplication_and_no_safety_promotion(self):
        data = {"records": [
            {"title": "Testudo <i>graeca</i> diet", "doi": "10.1/a", "source_key": "doi:10.1/a"},
            {"title": "Testudo graeca diet", "doi": "10.1/a", "source_key": "doi:10.1/a"},
            {"title": "Gopherus habitat", "doi": "10.1/b"},
            {"title": "Tortoise beetle feeding", "doi": "10.1/c"},
            {"title": "Kinixys foraging patterns", "doi": "10.1/d"}]}
        result = triage(data)
        self.assertEqual(result["input_records"], 5)
        self.assertEqual(result["deduplicated_titles"], 4)
        self.assertEqual(result["counts"], {
            "priority_review": 2, "context_review": 1,
            "exclude_from_feeding_review": 1})
        for group in result["groups"].values():
            for record in group:
                self.assertEqual(record["feeding_safety_status"], "unassessed")
                self.assertEqual(record["verified_plant_links"], [])

    def test_missing_title_not_accepted_as_evidence(self):
        result = triage({"records": [{"title": "", "doi": "10.1/missing"}]})
        self.assertEqual(result["counts"]["exclude_from_feeding_review"], 1)

if __name__ == "__main__":
    unittest.main()
