#!/usr/bin/env python3
"""Read-only progress summary while the 22k OpenAlex crawler is still running."""
import argparse
import json
from collections import Counter
from pathlib import Path

def main():
    p = argparse.ArgumentParser()
    p.add_argument('checkpoint', type=Path)
    p.add_argument('--catalog-size', type=int, default=22045)
    args = p.parse_args()
    if not args.checkpoint.exists():
        raise SystemExit('Checkpoint not yet created: ' + str(args.checkpoint))
    latest = {}
    malformed = 0
    with args.checkpoint.open('r', encoding='utf-8') as stream:
        for line in stream:
            try:
                row = json.loads(line)
                key = row['name'].strip().casefold()
                if not key:
                    raise ValueError('empty scientific name')
                if key not in latest or row.get('status') == 'searched':
                    latest[key] = row
            except (ValueError, KeyError, TypeError):
                malformed += 1
    counts = Counter(row.get('status') for row in latest.values())
    with_hits = sum(bool(row.get('hits')) for row in latest.values()
                    if row.get('status') == 'searched')
    report = {
        'target_unique_taxa': args.catalog_size,
        'processed_unique_taxa': len(latest),
        'searched_unique_taxa': counts['searched'],
        'retry_needed_unique_taxa': counts['retry_needed'],
        'remaining_unprocessed': max(0, args.catalog_size - len(latest)),
        'taxa_with_unreviewed_hits': with_hits,
        'total_unreviewed_hits': sum(len(row.get('hits') or []) for row in latest.values()
                                     if row.get('status') == 'searched'),
        'incomplete_lines': malformed,
        'new_verified_feeding_taxa': 0
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
