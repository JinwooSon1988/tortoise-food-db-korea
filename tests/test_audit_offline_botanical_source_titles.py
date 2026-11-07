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

if __name__=="__main__":
    unittest.main()
