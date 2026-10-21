#!/usr/bin/env python3
"""Summarize OpenAlex literature candidates without promoting them to evidence."""
import argparse
import json
from collections import Counter
from pathlib import Path

def main():
    p = argparse.ArgumentParser()
    p.add_argument('input', type=Path)
    p.add_argument('--report', type=Path)
    args = p.parse_args()
    latest = {}
    malformed = 0
    with args.input.open(encoding='utf-8') as stream:
        for line in stream:
            try:
                row = json.loads(line)
                name = row['name'].strip().casefold()
                if not name:
                    raise ValueError('blank name')
                # A later successful retry replaces earlier transient errors.
                if row.get('status') == 'searched' or name not in latest:
                    latest[name] = row
            except (ValueError, KeyError, TypeError):
                malformed += 1
    counts = Counter(row.get('status', 'unknown') for row in latest.values())
    hits = sum(len(row.get('hits') or []) for row in latest.values()
               if row.get('status') == 'searched')
    with_hits = sum(bool(row.get('hits')) for row in latest.values()
                    if row.get('status') == 'searched')
    report = {
        'distinct_taxa_processed': len(latest),
        'searched': counts['searched'],
        'retry_needed': counts['retry_needed'],
        'taxa_with_literature_candidates': with_hits,
        'literature_candidate_records': hits,
        'malformed_lines': malformed,
        'verified_feeding_taxa_from_this_search': 0,
        'note': 'Search matches are unreviewed leads, never verified feeding evidence.'
    }
    text = json.dumps(report, ensure_ascii=False, indent=2)
    print(text)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(text + '\n', encoding='utf-8')

if __name__ == '__main__':
    main()
