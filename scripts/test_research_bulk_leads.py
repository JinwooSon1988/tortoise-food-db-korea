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
        self.assertEqual(row['error'], 'http_404')
        self.assertEqual(request.call_count, 1)

    def test_http_429_retries_then_checkpoints_failure(self):
        error = HTTPError('https://api.openalex.org', 429, 'Rate Limited',
                          {'Retry-After': '1'}, None)
        with patch.object(crawler.urllib.request, 'urlopen', side_effect=error) as request:
            with patch.object(crawler.time, 'sleep'):
                row = crawler.query({'name': 'Plantago major', 'taxon_id': 'gbif:1'})
        self.assertEqual(row['status'], 'retry_needed')
        self.assertEqual(row['error'], 'http_429')
        self.assertEqual(request.call_count, 4)

if __name__ == '__main__':
    unittest.main()
