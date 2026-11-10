import unittest
from scripts.match_diet_titles_to_plant_catalog import match_titles

class TitleCatalogJoinTests(unittest.TestCase):
    def test_exact_binomial_only_and_no_safety_inference(self):
        plants = [{"id":"a","scientific":"Taraxacum officinale"},
                  {"id":"b","scientific":"Plantago major"}]
        triage = {"groups":{"priority_review":[
            {"title":"Testudo diet includes Taraxacum officinale and Plantago major",
             "doi":"10.1/example", "source_key":"doi:10.1/example"},
            {"title":"Testudo feeding Taraxacum species"}],
            "context_review":[], "exclude_from_feeding_review":[
            {"title":"Taraxacum officinale tortoise beetle feeding"}]}}
        result = match_titles(triage, plants)
        self.assertEqual(result["title_leads_scanned"], 2)
        self.assertEqual(result["candidate_matches"], 2)
        self.assertEqual({r["public_plant_id_candidates"][0] for r in result["records"]},{"a","b"})
        self.assertTrue(all(r["feeding_safety_status"]=="unassessed"
            and r["feeding_observation_status"]=="not_verified"
            and not r["verified_plant_links"] for r in result["records"]))

    def test_ambiguous_catalog_identity_is_not_silently_resolved(self):
        plants = [{"id":"a","scientific":"Plantago major"},
                  {"id":"b","scientific":"Plantago major"}]
        triage = {"groups":{"priority_review":[{"title":"Testudo diet Plantago major"}]}}
        result = match_titles(triage, plants)
        self.assertEqual(result["records"][0]["match_status"],"ambiguous_name")
        self.assertEqual(result["records"][0]["public_plant_id_candidates"],["a","b"])

if __name__ == "__main__":
    unittest.main()
