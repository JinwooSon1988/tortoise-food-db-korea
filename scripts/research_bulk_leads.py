#!/usr/bin/env python3
"""Checkpointed, bounded-concurrency OpenAlex discovery for tortoise diet plant leads.

This discovers literature CANDIDATES, not feeding evidence or safety grades.
Uses only Python standard library and a public API; respects HTTP 429 and retries.
Usage: python scripts/research_bulk_leads.py --workers 8 --limit 22045
Resume: rerun with the same --output; completed names are skipped.
"""
import argparse
import csv
import concurrent.futures
import json
import random
import re
import time
import threading
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEARCH = 'tortoise diet feeding'
_RATE_LOCK = threading.Lock()
_NEXT_REQUEST = 0.0
_REQUEST_INTERVAL = 3.0
_RATE_LIMITED = threading.Event()

def throttle():
    global _NEXT_REQUEST
    with _RATE_LOCK:
        if _RATE_LIMITED.is_set():
            return False
        now = time.monotonic()
        wait = max(0.0, _NEXT_REQUEST - now)
        _NEXT_REQUEST = max(now, _NEXT_REQUEST) + _REQUEST_INTERVAL
    if wait:
        time.sleep(wait)
    return not _RATE_LIMITED.is_set()

def load_taxa():
    seen = set()
    for path in sorted((ROOT / 'data/plant-catalog').glob('taxa-??.json')):
        for p in json.loads(path.read_text(encoding='utf-8'))['records']:
            name = p.get('scientific', '').strip()
            if name and name.casefold() not in seen:
                seen.add(name.casefold())
                yield {'name': name, 'taxon_id': p['id']}

def load_candidate_csv(path):
    """Stream the research-only taxonomy export without treating names as feeding evidence."""
    seen = set()
    with path.open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or 'plant_scientific_name' not in reader.fieldnames:
            raise ValueError('candidate CSV missing plant_scientific_name')
        for row in reader:
            name = (row.get('plant_scientific_name') or '').strip()
            if not re.fullmatch(r'[A-Z][a-z]+ [a-z][a-z-]+', name):
                raise ValueError(f'invalid research candidate binomial: {name!r}')
            key = name.casefold()
            if key not in seen:
                seen.add(key)
                yield {'name': name, 'taxon_id': None}


def load_completed_checkpoint(path):
    """Read durable JSONL rows; repair only a truncated final row after interruption."""
    completed = set()
    if not path.exists():
        return completed
    with path.open('rb+') as stream:
        line_number = 0
        while True:
            offset = stream.tell()
            line = stream.readline()
            if not line:
                break
            line_number += 1
            complete_line = line.endswith(b'\n')
            try:
                row = json.loads(line)
            except (UnicodeDecodeError, ValueError) as exc:
                if not complete_line:
                    # Only an invalid unterminated tail may be discarded.
                    stream.truncate(offset)
                    break
                raise ValueError(f'corrupt completed checkpoint line {line_number}') from exc
            if not complete_line:
                # A valid final JSON object is durable; retain it and make appends safe.
                stream.seek(0, 2)
                stream.write(b'\n')
            if not isinstance(row, dict) or row.get('status') not in ('searched', 'retry_needed'):
                raise ValueError(f'invalid checkpoint status on line {line_number}')
            name = row.get('name')
            if not isinstance(name, str) or not name.strip():
                raise ValueError(f'missing checkpoint taxon on line {line_number}')
            if row['status'] == 'searched':
                completed.add(name.casefold())
    return completed


def query(taxon, timeout=20):
    name = taxon['name']
    params = urllib.parse.urlencode({
        'search': f'"{name}" {SEARCH}', 'per-page': '5',
        'select': 'id,doi,title,publication_year,primary_location,authorships',
    })
    url = 'https://api.openalex.org/works?' + params
    for attempt in range(4):
        if not throttle():
            return {**taxon, 'status': 'retry_needed', 'error': 'rate_limit_circuit_open', 'hits': []}
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
            if exc.code == 429:
                _RATE_LIMITED.set()
                return {**taxon, 'status': 'retry_needed', 'error': 'HTTP_429', 'hits': []}
            if attempt == 3:
                return {**taxon, 'status': 'retry_needed', 'error': f'HTTP_{exc.code}', 'hits': []}
            time.sleep(min(30, 2 ** attempt + random.random()))
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            if attempt == 3:
                return {**taxon, 'status': 'retry_needed', 'error': type(exc).__name__,
                        'hits': []}
            time.sleep(min(30, 2 ** attempt + random.random()))
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--workers', type=int, default=1)
    ap.add_argument('--taxa-csv', type=Path, help='Research-only candidate CSV from export_candidate_taxonomy_for_research.py')
    ap.add_argument('--request-interval', type=float, default=3.0)
    ap.add_argument('--limit', type=int, default=22045)
    ap.add_argument('--offset', type=int, default=0, help='Skip this many unique source taxa before applying limit')
    ap.add_argument('--output', type=Path, default=ROOT / 'data/research/openalex-tortoise-leads.jsonl')
    args = ap.parse_args()
    global _REQUEST_INTERVAL
    if args.request_interval < 1.0:
        ap.error('--request-interval must be at least 1 second')
    _REQUEST_INTERVAL = args.request_interval
    if args.limit < 1:
        ap.error('--limit must be positive')
    if args.offset < 0:
        ap.error('--offset must be nonnegative')
    if args.workers < 1 or args.workers > 12:
        ap.error('--workers must be between 1 and 12 to avoid API abuse')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    completed = load_completed_checkpoint(args.output)
    if args.limit > 500:
        print('WARNING: limit above 500 may exhaust OpenAlex quota; prefer literature-first extraction.', flush=True)
    source_taxa = load_candidate_csv(args.taxa_csv) if args.taxa_csv else load_taxa()
    taxa = []
    for index, t in enumerate(source_taxa):
        if index < args.offset:
            continue
        if t['name'].casefold() not in completed:
            taxa.append(t)
            if len(taxa) >= args.limit:
                break
    counts = {'searched': 0, 'retry_needed': 0, 'hit_leads': 0}
    # Bounded submissions: never queue all 22k requests before the first result.
    # Once OpenAlex returns 429, stop scheduling and leave the rest for a later run.
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        source = iter(taxa)
        pending = {}
        with args.output.open('a', encoding='utf-8') as stream:
            while not _RATE_LIMITED.is_set() and len(pending) < args.workers:
                t = next(source, None)
                if t is None:
                    break
                pending[pool.submit(query, t)] = t
            while pending:
                done, _ = concurrent.futures.wait(pending, return_when=concurrent.futures.FIRST_COMPLETED)
                for future in done:
                    pending.pop(future)
                    row = future.result()
                    stream.write(json.dumps(row, ensure_ascii=False) + '\n')
                    stream.flush()
                    counts[row['status']] += 1
                    counts['hit_leads'] += len(row['hits'])
                    if (counts['searched'] + counts['retry_needed']) % 100 == 0:
                        print(json.dumps(counts, ensure_ascii=False), flush=True)
                while not _RATE_LIMITED.is_set() and len(pending) < args.workers:
                    t = next(source, None)
                    if t is None:
                        break
                    pending[pool.submit(query, t)] = t
    if _RATE_LIMITED.is_set():
        print('HTTP 429: stopped further submissions; retry after provider cooldown.', flush=True)
    print(json.dumps({'previously_completed': len(completed), **counts}, ensure_ascii=False))
if __name__ == '__main__':
    main()
