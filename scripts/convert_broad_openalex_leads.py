#!/usr/bin/env python3
"""Convert broad OpenAlex title matches to exact-name per-taxon lead JSONL.

Use with merge_openalex_leads.py. This does not verify feeding or safety.
"""
import argparse
import json
from collections import defaultdict
from pathlib import Path

def convert(source):
    by_name = defaultdict(dict)
    pages = 0
    failed = 0
    with source.open(encoding='utf-8') as stream:
        for line in stream:
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if row.get('status') != 'searched':
                failed += 1
                continue
            pages += 1
            for work in row.get('matched_title_leads') or []:
                title = (work.get('title') or '').strip()
                if not title or 'tortoise beetle' in title.casefold():
                    continue
                url = work.get('doi') or work.get('openalex_id')
                if not isinstance(url, str) or not url.startswith('https://'):
                    continue
                for name in work.get('matched_title_names') or []:
                    name = name.strip()
                    if not name:
                        continue
                    key = (url.casefold(), title.casefold())
                    by_name[name.casefold()][key] = {
                        'title': title, 'doi': work.get('doi'),
                        'openalex_id': work.get('openalex_id'),
                        'year': work.get('year'),
                        'status': 'literature_lead_unreviewed'}
    rows = [{'name': name, 'status': 'searched', 'hits': list(hits.values())}
            for name, hits in sorted(by_name.items())]
    return rows, {'pages_processed': pages, 'pages_failed': failed,
                  'taxa_with_title_matched_candidates': len(rows),
                  'unreviewed_candidates': sum(len(r['hits']) for r in rows)}

def main():
    p = argparse.ArgumentParser()
    p.add_argument('source', type=Path)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    rows, stats = convert(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('w', encoding='utf-8') as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False) + '\n')
    print(json.dumps(stats, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
