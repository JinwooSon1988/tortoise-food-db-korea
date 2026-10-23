#!/usr/bin/env python3
"""Checkpointed, bounded-concurrency OpenAlex discovery for tortoise diet plant leads.

This discovers literature CANDIDATES, not feeding evidence or safety grades.
Uses only Python standard library and a public API. Requests go through scripts/polite_http.py (robots.txt, the
OpenAlex rate limit, Retry-After on 429, retries, and a provenance log next to --output).
Usage: python scripts/research_bulk_leads.py --workers 8 --limit 22045
Resume: rerun with the same --output; completed names are skipped.
"""
import argparse
import concurrent.futures
import json
import re
import time
import sys
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from polite_http import PoliteClient, FetchError, RobotsDisallowed  # noqa: E402
CLIENT = None
SEARCH = 'tortoise diet feeding'
def load_taxa():
    seen = set()
    for path in sorted((ROOT / 'data/plant-catalog').glob('taxa-??.json')):
        for p in json.loads(path.read_text(encoding='utf-8'))['records']:
            name = p.get('scientific', '').strip()
            if name and name.casefold() not in seen:
                seen.add(name.casefold())
                yield {'name': name, 'taxon_id': p['id']}

def query(taxon, timeout=20):
    name = taxon['name']
    params = urllib.parse.urlencode({
        'search': f'"{name}" {SEARCH}', 'per-page': '5',
        'select': 'id,doi,title,publication_year,primary_location,authorships',
    })
    url = 'https://api.openalex.org/works?' + params
    for attempt in range(1):
        try:
            raw, _ = CLIENT.get_json(url, purpose='openalex lead discovery')
            hits = []
            for work in raw.get('results', []):
                title = work.get('title') or ''
                # A search hit is NOT a confirmed feeding record; preserve as a lead.
                hits.append({
                    'openalex_id': work.get('id'), 'doi': work.get('doi'),
                    'title': title, 'year': work.get('publication_year'),
                    'source_url': (work.get('primary_location') or {}).get('landing_page_url'),
                    'status': 'literature_lead_unreviewed',
                })
            return {**taxon, 'status': 'searched', 'query': f'"{name}" {SEARCH}',
                    'hits': hits, 'searched_at_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
        except (FetchError, RobotsDisallowed, ValueError) as exc:  # the client already retried transient errors
            return {**taxon, 'status': 'retry_needed', 'error': type(exc).__name__, 'hits': []}
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--workers', type=int, default=6)
    ap.add_argument('--limit', type=int, default=22045)
    ap.add_argument('--output', type=Path, default=ROOT / 'data/research/openalex-tortoise-leads.jsonl')
    args = ap.parse_args()
    if args.workers < 1 or args.workers > 12:
        ap.error('--workers must be between 1 and 12 to avoid API abuse')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    global CLIENT
    CLIENT = PoliteClient(provenance=args.output.with_name(args.output.stem + '.requests.jsonl'))
    completed = set()
    if args.output.exists():
        for line in args.output.read_text(encoding='utf-8').splitlines():
            try:
                row = json.loads(line)
                if row.get('status') == 'searched':
                    completed.add(row['name'].casefold())
            except (ValueError, KeyError):
                pass
    taxa = [t for t in load_taxa() if t['name'].casefold() not in completed][:args.limit]
    counts = {'searched': 0, 'retry_needed': 0, 'hit_leads': 0}
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        pending = {pool.submit(query, t): t for t in taxa}
        with args.output.open('a', encoding='utf-8') as stream:
            for future in concurrent.futures.as_completed(pending):
                row = future.result()
                stream.write(json.dumps(row, ensure_ascii=False) + '\n')
                stream.flush()
                counts[row['status']] += 1
                counts['hit_leads'] += len(row['hits'])
                if (counts['searched'] + counts['retry_needed']) % 100 == 0:
                    print(json.dumps(counts, ensure_ascii=False), flush=True)
    print(json.dumps({'previously_completed': len(completed), **counts}, ensure_ascii=False))
if __name__ == '__main__':
    main()
