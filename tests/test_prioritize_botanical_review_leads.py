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

if __name__=="__main__":
    unittest.main()
