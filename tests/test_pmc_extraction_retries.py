import io
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from scripts.extract_jats_botanical_mentions import scan

ARTICLE=b'<article><body><p>Rumex crispus was observed.</p></body></article>'
RECORD={"pmcid":"PMC123","source_url":"https://example.org/article"}

class RetryTests(unittest.TestCase):
    def test_transient_error_recovers(self):
        with patch("scripts.extract_jats_botanical_mentions.urllib.request.urlopen",
                   side_effect=[HTTPError("u",503,"unavailable",{},None),io.BytesIO(ARTICLE)]) as urlopen, \
             patch("scripts.extract_jats_botanical_mentions.time.sleep") as sleep:
            result=scan(RECORD)
        self.assertEqual(result["status"],"scanned")
        self.assertEqual(result["attempts"],2)
        self.assertEqual(urlopen.call_count,2)
        sleep.assert_called_once()

    def test_permanent_error_does_not_retry(self):
        with patch("scripts.extract_jats_botanical_mentions.urllib.request.urlopen",
                   side_effect=HTTPError("u",404,"missing",{},None)) as urlopen:
            result=scan(RECORD)
        self.assertEqual(result["status"],"http_404")
        self.assertEqual(result["attempts"],1)
        self.assertEqual(urlopen.call_count,1)

if __name__=="__main__":
    unittest.main()
