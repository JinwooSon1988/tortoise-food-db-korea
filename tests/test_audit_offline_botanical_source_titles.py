import unittest
from scripts.audit_offline_botanical_source_titles import audit

class OfflineTitleAuditTests(unittest.TestCase):
    def test_tortoise_beetle_is_not_a_tortoise(self):
        discovery={"records":[{"source_url":"a","title":"Tortoise beetle feeding on plants"}]}
        prioritized={"records":[{"source_url":"a","candidate_plant_name":"Chenopodium album",
                                "mention_count":1,"public_plant_id_candidates":["plant"]}]}
        result=audit(discovery,prioritized)
        self.assertEqual(result["signal_counts"]["tortoise_diet_title"],0)
        self.assertEqual(result["signal_counts"]["other_title"],1)

    def test_relevance_is_review_only(self):
        discovery={"records":[
            {"source_url":"a","title":"Testudo graeca feeding ecology"},
            {"source_url":"b","title":"Rumex crispus biomass"},
            {"source_url":"c","title":"Gopher tortoise habitat"}]}
        prioritized={"records":[
            {"source_url":url,"candidate_plant_name":name,"mention_count":count,
             "public_plant_id_candidates":["plant"]}
            for url,name,count in [("b","Rumex crispus",10),("c","Poa annua",2),
                                   ("a","Plantago major",1)]]}
        result=audit(discovery,prioritized)
        self.assertEqual(result["review_pairs"],3)
        self.assertEqual(result["signal_counts"],{
            "tortoise_diet_title":1,"tortoise_title":1,"other_title":1})
        self.assertEqual(result["records"][0]["candidate_plant_name"],"Plantago major")
        self.assertTrue(all(r["feeding_observation_status"]=="not_verified"
                            and r["feeding_safety_status"]=="unassessed"
                            and not r["verified_plant_links"] for r in result["records"]))

    def test_context_cues_rank_within_same_title_tier_without_promoting_safety(self):
        discovery={"records":[{"source_url":"a","title":"Plant ecology"},
                              {"source_url":"b","title":"Plant ecology"}]}
        prioritized={"records":[
            {"source_url":"a","candidate_plant_name":"Plantago major",
             "mention_count":50,"public_plant_id_candidates":["plant"],
             "review_priority_signal":"no_keyword_signal"},
            {"source_url":"b","candidate_plant_name":"Poa annua",
             "mention_count":1,"public_plant_id_candidates":["plant"],
             "review_priority_signal":"tortoise_and_feeding_keywords"}]}
        result=audit(discovery,prioritized)
        self.assertEqual(result["records"][0]["source_url"],"b")
        self.assertEqual(result["context_signal_counts"]["tortoise_and_feeding_keywords"],1)
        self.assertTrue(all(r["feeding_safety_status"]=="unassessed"
                            and not r["verified_plant_links"] for r in result["records"]))

if __name__=="__main__":
    unittest.main()
