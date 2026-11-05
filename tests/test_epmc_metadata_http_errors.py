import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from scripts.discover_research_sources_epmc import lookup

RECORD={"source_url":"https://doi.org/10.1234/test","title":"Example","taxon_associations":[]}

class MetadataHttpErrors(unittest.TestCase):
    def test_permanent_403_is_recorded_without_retries(self):
        with patch("scripts.discover_research_sources_epmc.urllib.request.urlopen",
                   side_effect=HTTPError("url",403,"Forbidden",{},None)) as fetch:
            result=lookup(RECORD,retries=2)
        self.assertEqual(result["discovery_status"],"lookup_error")
        self.assertEqual(result["http_status"],403)
        self.assertEqual(result["attempts"],1)
        self.assertEqual(fetch.call_count,1)

    def test_transient_503_is_retried_boundedly(self):
        with patch("scripts.discover_research_sources_epmc.urllib.request.urlopen",
                   side_effect=HTTPError("url",503,"Unavailable",{},None)) as fetch, \
             patch("scripts.discover_research_sources_epmc.time.sleep"):
            result=lookup(RECORD,retries=2)
        self.assertEqual(result["http_status"],503)
        self.assertEqual(result["attempts"],3)
        self.assertEqual(fetch.call_count,3)

if __name__=="__main__":
    unittest.main()
