#!/usr/bin/env python3
"""Regression tests for exact-match, safe, idempotent bulk lead ingestion."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

module_path = Path(__file__).with_name('merge_openalex_leads.py')
spec = importlib.util.spec_from_file_location('merge_leads', module_path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class MergeTests(unittest.TestCase):
    def test_exact_name_dedup_and_no_safety_grade(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            catalog = root / 'data/plant-catalog'
            catalog.mkdir(parents=True)
            (catalog / 'taxa-00.json').write_text(json.dumps({'records': [
                {'id': 'gbif:1', 'scientific': 'Plantago major'},
                {'id': 'gbif:2', 'scientific': 'Plantago lanceolata'}]}))
            existing = root / 'existing.json'
            existing.write_text(json.dumps({'taxa': {}}))
            source = root / 'leads.jsonl'
            source.write_text(json.dumps({'name': 'Plantago major', 'status': 'searched',
                'hits': [{'title': 'A study', 'doi': 'https://doi.org/10.1/example',
                          'year': 2023}]}) + '\n')
            with patch.object(mod, 'ROOT', root):
                result, stats = mod.build(source, existing)
                again = root / 'again.json'
                again.write_text(json.dumps(result))
                second, stats2 = mod.build(source, again)
        self.assertEqual(stats['new_unreviewed_leads'], 1)
        self.assertEqual(stats2['new_unreviewed_leads'], 0)
        lead = second['taxa']['gbif:1']['literature_leads'][0]
        self.assertEqual(lead['verification'], 'search_hit_unreviewed')
        self.assertEqual(lead['feeding_safety_status'], 'unassessed')
        self.assertNotIn('safety_grade', lead)
        self.assertNotIn('gbif:2', second['taxa'])

if __name__ == '__main__':
    unittest.main()
