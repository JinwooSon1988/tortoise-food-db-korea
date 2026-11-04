import unittest
from scripts.join_botanical_mentions_to_public_plants import join

class JoinTests(unittest.TestCase):
    def test_exact_match_only_and_fail_closed(self):
        plants=[{"id":"a","scientific":"Mirabilis laevis"},
                {"id":"b","scientific":"Cichorium intybus"}]
        def mention(name):
            return {"source_url":"https://example.org/a","pmcid":"PMC1",
                    "candidate_plant_name":name,"exact_context_excerpt":name}
        rows=join([mention("Mirabilis laevis"),mention("Mirabilis"),mention("Cichorium intybus")],plants)
        self.assertEqual(rows[0]["public_plant_id_candidates"],["a"])
        self.assertEqual(rows[1]["public_plant_id_candidates"],[])
        self.assertEqual(rows[2]["public_plant_id_candidates"],["b"])
        self.assertTrue(all(r["feeding_safety_status"]=="unassessed" and
                            r["feeding_observation_status"]=="not_verified" and
                            not r["verified_plant_links"] for r in rows))
    def test_duplicate_scientific_name_is_ambiguous(self):
        plants=[{"id":"a","scientific":"Mirabilis laevis"},{"id":"b","scientific":"Mirabilis laevis"}]
        mention={"source_url":"x","pmcid":"PMC1","candidate_plant_name":"Mirabilis laevis",
                 "exact_context_excerpt":"Mirabilis laevis"}
        self.assertEqual(join([mention],plants)[0]["match_status"],"ambiguous_name")

if __name__=="__main__":
    unittest.main()
