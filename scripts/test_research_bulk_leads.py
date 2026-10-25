#!/usr/bin/env python3
"""Offline smoke tests for the resumable bulk research crawler."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

MODULE = Path(__file__).with_name('research_bulk_leads.py')
spec = importlib.util.spec_from_file_location('bulk_research', MODULE)
crawler = importlib.util.module_from_spec(spec)
spec.loader.exec_module(crawler)

class BulkResearchTests(unittest.TestCase):
    def setUp(self):
        # The crawler keeps a process-wide 429 circuit and request spacing; every test starts from a fresh state.
        crawler._RATE_LIMITED.clear()
        crawler._NEXT_REQUEST = 0.0
        patcher = patch.object(crawler.time, 'sleep')
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_success_is_only_an_unreviewed_lead(self):
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): return False
        with patch.object(crawler.urllib.request, 'urlopen', return_value=Response()):
            with patch.object(crawler.json, 'load', return_value={'results': [
                {'id': 'https://openalex.org/W123', 'title': 'A title', 'doi': None,
                 'publication_year': 2024, 'primary_location': {}}]}):
                row = crawler.query({'name': 'Plantago major', 'taxon_id': 'gbif:1'})
        self.assertEqual(row['status'], 'searched')
        self.assertEqual(row['hits'][0]['status'], 'literature_lead_unreviewed')
        self.assertNotIn('safety_grade', row)

    def test_http_404_is_retry_needed_without_retries(self):
        error = HTTPError('https://api.openalex.org', 404, 'Not Found', {}, None)
        with patch.object(crawler.urllib.request, 'urlopen', side_effect=error) as request:
            row = crawler.query({'name': 'Plantago major', 'taxon_id': 'gbif:1'})
        self.assertEqual(row['status'], 'retry_needed')
        self.assertEqual(row['error'], 'HTTP_404')
        self.assertEqual(request.call_count, 1)

    def test_http_429_opens_circuit_without_retrying(self):
        # Owner's rule on main (f53ced15): a 429 is a quota signal - stop at once, checkpoint, send nothing more.
        error = HTTPError('https://api.openalex.org', 429, 'Rate Limited',
                          {'Retry-After': '1'}, None)
        with patch.object(crawler.urllib.request, 'urlopen', side_effect=error) as request:
            row = crawler.query({'name': 'Plantago major', 'taxon_id': 'gbif:1'})
            later = crawler.query({'name': 'Plantago lanceolata', 'taxon_id': 'gbif:2'})
        self.assertEqual(row['status'], 'retry_needed')
        self.assertEqual(row['error'], 'HTTP_429')
        self.assertEqual(later['error'], 'rate_limit_circuit_open')
        self.assertEqual(request.call_count, 1)

if __name__ == '__main__':
    unittest.main()
