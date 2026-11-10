import unittest
from scripts.check_pmc_fulltext_parallel import merge_retry_results, eligible_for_second_pass

class SelectiveRetryTests(unittest.TestCase):
    def test_recovered_error_keeps_other_sources_and_order(self):
        prior={"total_candidates":3,"status_counts":{"full_text_xml_available":1,"request_error":1,"full_text_unavailable":1},
               "records":[{"source_url":"a","status":"full_text_xml_available"},
                          {"source_url":"b","status":"request_error"},
                          {"source_url":"c","status":"full_text_unavailable"}]}
        merged=merge_retry_results(prior,[{"source_url":"b","status":"full_text_xml_available"}])
        self.assertEqual([r["source_url"] for r in merged["records"]],["a","b","c"])
        self.assertEqual(merged["status_counts"],{"full_text_xml_available":2,"full_text_unavailable":1})
        self.assertEqual(merged["retry_attempted"],1)
        self.assertEqual(merged["retry_recovered"],1)
        self.assertEqual(prior["records"][1]["status"],"request_error")

    def test_persistent_500_skips_redundant_second_pass(self):
        prior={"records":[{"source_url":"a","status":"request_error","http_status":500},
                          {"source_url":"b","status":"request_error"},
                          {"source_url":"c","status":"request_error","http_status":503}]}
        self.assertFalse(eligible_for_second_pass(prior["records"][0]))
        self.assertTrue(eligible_for_second_pass(prior["records"][1]))
        self.assertTrue(eligible_for_second_pass(prior["records"][2]))
        merged=merge_retry_results(prior,[{"source_url":"b","status":"full_text_xml_available"},
                                          {"source_url":"c","status":"request_error","http_status":503}])
        self.assertEqual(merged["retry_attempted"],2)
        self.assertEqual(merged["retry_skipped_http_500"],1)
        self.assertEqual(merged["retry_recovered"],1)
        self.assertEqual(merged["records"][0]["http_status"],500)

    def test_rejects_retry_overwriting_success(self):
        prior={"records":[{"source_url":"a","status":"full_text_xml_available"}]}
        with self.assertRaises(AssertionError):
            merge_retry_results(prior,[{"source_url":"a","status":"request_error"}])

if __name__=="__main__":
    unittest.main()
