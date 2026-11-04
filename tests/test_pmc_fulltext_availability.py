#!/usr/bin/env python3
"""Offline contract tests for PMC XML availability classification."""
import io
import unittest
from unittest.mock import patch
from scripts.check_pmc_fulltext_parallel import check

class FakeResponse:
    def __init__(self, body):
        self.body = body
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self, n):
        return self.body[:n]

class AvailabilityTests(unittest.TestCase):
    def setUp(self):
        self.record = {"source_url": "https://doi.org/10.1000/test", "pmcid": "PMC12345"}
    def test_article(self):
        body = b'<article><body><sec><title>Diet</title></sec><sec/></body></article>'
        with patch("scripts.check_pmc_fulltext_parallel.urllib.request.urlopen", return_value=FakeResponse(body)):
            result = check(self.record, retries=0)
        self.assertEqual(result["status"], "full_text_xml_available")
        self.assertEqual(result["article_sections"], 2)
        self.assertEqual(result["plant_associations_verified"], 0)
        self.assertEqual(result["feeding_safety_status"], "unassessed")
    def test_invalid_xml(self):
        with patch("scripts.check_pmc_fulltext_parallel.urllib.request.urlopen", return_value=FakeResponse(b"<article>")):
            self.assertEqual(check(self.record, retries=0)["status"], "invalid_xml")
    def test_unexpected_root(self):
        with patch("scripts.check_pmc_fulltext_parallel.urllib.request.urlopen", return_value=FakeResponse(b"<error/>")):
            self.assertEqual(check(self.record, retries=0)["status"], "unexpected_xml_root")
    def test_invalid_identifier(self):
        self.assertEqual(check({**self.record, "pmcid": "1234"}, retries=0)["status"], "invalid_pmcid")

if __name__ == "__main__":
    unittest.main()
