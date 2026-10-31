#!/usr/bin/env python3
"""Unit tests for checkpoint report deduplication and retry accounting."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name('report_bulk_leads.py')

class CoverageReportTests(unittest.TestCase):
    def test_successful_retry_supersedes_error_and_deduplicates(self):
        rows = [
            {'name': 'Plantago major', 'status': 'retry_needed', 'hits': []},
            {'name': 'Plantago major', 'status': 'searched',
             'hits': [{'status': 'literature_lead_unreviewed'}]},
            {'name': 'PLANTAGO MAJOR', 'status': 'retry_needed', 'hits': []},
            {'name': 'Taraxacum officinale', 'status': 'searched', 'hits': []}
        ]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'leads.jsonl'
            path.write_text(''.join(json.dumps(row) + '\n' for row in rows),
                            encoding='utf-8')
            result = subprocess.run([sys.executable, str(SCRIPT), str(path)],
                                    check=True, capture_output=True, text=True)
            report = json.loads(result.stdout)
        self.assertEqual(report['distinct_taxa_processed'], 2)
        self.assertEqual(report['searched'], 2)
        self.assertEqual(report['retry_needed'], 0)
        self.assertEqual(report['taxa_with_literature_candidates'], 1)
        self.assertEqual(report['verified_feeding_taxa_from_this_search'], 0)

if __name__ == '__main__':
    unittest.main()
