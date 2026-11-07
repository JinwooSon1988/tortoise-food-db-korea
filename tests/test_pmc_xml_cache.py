import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from scripts.check_pmc_fulltext_parallel import check
from scripts.extract_jats_botanical_mentions import scan

XML=b'<article><body><sec><p>Plantago major was measured.</p></sec></body></article>'
RECORD={"source_url":"https://doi.org/10.1234/test","pmcid":"PMC12345"}

class FakeResponse:
    def __enter__(self): return self
    def __exit__(self,*args): return False
    def read(self,limit): return XML

class PmcXmlCacheTests(unittest.TestCase):
    def test_validated_xml_reused_without_second_request(self):
        with tempfile.TemporaryDirectory() as d:
            with patch("scripts.check_pmc_fulltext_parallel.urllib.request.urlopen",return_value=FakeResponse()) as fetch:
                result=check(RECORD,cache_dir=d)
            self.assertEqual(result["status"],"full_text_xml_available")
            self.assertEqual(fetch.call_count,1)
            self.assertEqual((Path(d)/"PMC12345.xml").read_bytes(),XML)
            with patch("scripts.extract_jats_botanical_mentions.urllib.request.urlopen",side_effect=AssertionError("network should not be used")):
                extracted=scan(RECORD,cache_dir=d)
            self.assertEqual(extracted["status"],"scanned")
            self.assertEqual(extracted["attempts"],0)
            self.assertEqual(extracted["candidates"][0]["candidate_plant_name"],"Plantago major")
            self.assertEqual(extracted["candidates"][0]["feeding_safety_status"],"unassessed")

if __name__=="__main__":
    unittest.main()
