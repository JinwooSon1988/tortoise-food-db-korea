#!/usr/bin/env python3
"""Checkpointed, bounded-concurrency OpenAlex discovery for tortoise diet plant leads.

This discovers literature CANDIDATES, not feeding evidence or safety grades.
Uses only Python standard library and a public API; respects HTTP 429 and retries.
Usage: python scripts/research_bulk_leads.py --workers 8 --limit 22045
Resume: rerun with the same --output; completed names are skipped.
"""
import argparse
import concurrent.futures
import json
import random
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
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
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'GeobukbapResearch/0.1 (literature lead discovery; contact via repository issues)',
                'Accept': 'application/json',
            })
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = json.load(resp)
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
        except urllib.error.HTTPError as exc:
            if exc.code in (429, 503) and attempt < 3:
                retry_after = exc.headers.get('Retry-After', '')
                delay = int(retry_after) if retry_after.isdigit() else 2 ** (attempt + 2)
                time.sleep(min(120, max(1, delay)) + random.random())
                continue
            return {**taxon, 'status': 'retry_needed',
                    'error': f'http_{exc.code}', 'hits': []}
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            if attempt == 3:
                return {**taxon, 'status': 'retry_needed', 'error': type(exc).__name__,
                        'hits': []}
            time.sleep(min(30, 2 ** attempt + random.random()))
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--workers', type=int, default=6)
    ap.add_argument('--limit', type=int, default=22045)
    ap.add_argument('--output', type=Path, default=ROOT / 'data/research/openalex-tortoise-leads.jsonl')
    args = ap.parse_args()
    if args.workers < 1 or args.workers > 12:
        ap.error('--workers must be between 1 and 12 to avoid API abuse')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    completed = set()
    if args.output.exists():
        for line in args.output.read_text(encoding='utf-8').splitlines():
            try:
                row = json.loads(line)
                if row.get('status') == 'searched':
                    completed.add(row['name'].casefold())
            except (ValueError, KeyError):
                pass
    # Deduplicate work within a run and retry only unresolved names.
    taxa = [t for t in load_taxa() if t['name'].casefold() not in completed][:args.limit]
    print(json.dumps({'catalog_candidates': len(taxa), 'already_searched': len(completed),
                      'workers': args.workers, 'output': str(args.output)},
                     ensure_ascii=False), flush=True)
    counts = {'searched': 0, 'retry_needed': 0, 'hit_leads': 0}
    # Rolling bounded queue: slow requests never hold up the next 4*workers batch.
    # Only the main thread writes the checkpoint, preserving JSONL integrity.
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        iterator = iter(taxa)
        pending = set()
        def submit_next():
            try:
                taxon = next(iterator)
            except StopIteration:
                return False
            pending.add(pool.submit(query, taxon))
            return True
        for _ in range(min(len(taxa), args.workers * 4)):
            submit_next()
        with args.output.open('a', encoding='utf-8') as stream:
            while pending:
                done, pending = concurrent.futures.wait(
                    pending, return_when=concurrent.futures.FIRST_COMPLETED)
                for future in done:
                    row = future.result()
                    stream.write(json.dumps(row, ensure_ascii=False) + '\n')
                    stream.flush()
                    counts[row['status']] += 1
                    counts['hit_leads'] += len(row['hits'])
                    if (counts['searched'] + counts['retry_needed']) % 100 == 0:
                        print(json.dumps(counts, ensure_ascii=False), flush=True)
                    submit_next()
    print(json.dumps({'previously_completed': len(completed), **counts}, ensure_ascii=False))
if __name__ == '__main__':
    main()
