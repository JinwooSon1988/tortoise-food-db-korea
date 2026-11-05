import unittest
from scripts.prioritize_botanical_review_leads import prioritize

class ReviewPriorityTests(unittest.TestCase):
    def test_dedup_preserves_counts_and_unverified_status(self):
        def row(name,url,status="exact_name_candidate"):
            return {"candidate_plant_name":name,"source_url":url,"pmcid":"PMC1",
                    "public_plant_id_candidates":["a"],"match_status":status,
                    "exact_context_excerpt":name,"name_start_offset":0}
        data={"total_mentions":4,"records":[row("Rumex crispus","u"),row("Rumex crispus","u"),
               row("Zea mays","v"),row("Type species","w","no_exact_name_match")]}
        result=prioritize(data)
        self.assertEqual(result["review_pairs"],2)
        self.assertEqual(result["unique_names"],2)
        self.assertEqual(result["unique_sources"],2)
        self.assertEqual(result["records"][0]["mention_count"],2)
        self.assertTrue(all(not r["verified_plant_links"] and r["feeding_safety_status"]=="unassessed" for r in result["records"]))

    def test_context_priority_never_verifies_feeding(self):
        def row(name,context,url):
            return {"candidate_plant_name":name,"source_url":url,"pmcid":"PMC1",
                    "public_plant_id_candidates":["a"],"match_status":"exact_name_candidate",
                    "exact_context_excerpt":context,"name_start_offset":0}
        data={"total_mentions":4,"records":[
            row("Zea mays","Zea mays measured in soil.","a"),
            row("Rumex crispus","Testudo graeca feeding on Rumex crispus.","b"),
            row("Plantago major","Plantago major was consumed by an unknown animal.","c"),
            row("Poa annua","Tortoise beetle found on Poa annua.","d")]}
        result=prioritize(data)
        self.assertEqual(result["records"][0]["candidate_plant_name"],"Rumex crispus")
        self.assertEqual(result["records"][0]["review_priority_signal"],"tortoise_and_feeding_keywords")
        beetle=next(r for r in result["records"] if r["candidate_plant_name"]=="Poa annua")
        self.assertEqual(beetle["tortoise_keyword_contexts"],0)
        self.assertTrue(all(r["feeding_observation_status"]=="not_verified" and
                            r["feeding_safety_status"]=="unassessed" and
                            not r["review_priority_is_evidence"] for r in result["records"]))

if __name__=="__main__":
    unittest.main()
