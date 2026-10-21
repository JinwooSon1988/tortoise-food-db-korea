#!/usr/bin/env python3
"""Low-request OpenAlex discovery: search broad tortoise diet literature by pages.

One search page can provide up to 200 papers. Plant names are matched only as
literal binomials in titles; results remain UNREVIEWED literature candidates.
No feeding/safety grades are inferred. Resume with --output; pages are recorded
as separate JSONL checkpoints. Does not write to the per-taxon crawler file.
"""
import argparse
import json
import random
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUERIES = [
    'tortoise diet plant feeding',
    'Testudo diet vegetation plants',
    'Geochelone diet plant',
    'Chelonoidis diet plants',
    'Aldabrachelys grazing diet',
    'Centrochelys sulcata forage diet',
    'Stigmochelys pardalis vegetation diet',
    'Astrochelys radiata diet plant',
]
def catalog_names():
    names = set()
    for path in sorted((ROOT / 'data/plant-catalog').glob('taxa-??.json')):
        for item in json.loads(path.read_text(encoding='utf-8'))['records']:
            name = (item.get('scientific') or '').strip()
            parts = name.split()
            if len(parts) >= 2 and re.fullmatch(r'[A-Z][a-z-]+', parts[0]) and re.fullmatch(r'[a-z-]+', parts[1]):
                names.add(' '.join(parts[:2]))
    return sorted(names)

def fetch_page(query, page, timeout=30):
    params = urllib.parse.urlencode({
        'search': query, 'per-page': 200, 'page': page,
        'select': 'id,doi,title,publication_year,primary_location',
    })
    url = 'https://api.openalex.org/works?' + params
    for attempt in range(2):
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'GeobukbapResearch/0.2 (public literature discovery)',
                'Accept': 'application/json'})
            with urllib.request.urlopen(req, timeout=timeout) as response:
                data = json.load(response)
            return {'status': 'searched', 'query': query, 'page': page,
                    'works': data.get('results') or []}
        except urllib.error.HTTPError as error:
            # 429 is a quota/rate-limit signal. Retrying the same provider
            # blocks the fallback for minutes without improving throughput.
            if error.code == 429:
                return {'status': 'retry_needed', 'query': query, 'page': page,
                        'error': 'http_429', 'works': []}
            if error.code == 503 and attempt < 1:
                time.sleep(3 + random.random())
                continue
            return {'status': 'retry_needed', 'query': query, 'page': page,
                    'error': 'http_' + str(error.code), 'works': []}
        except (urllib.error.URLError, TimeoutError, ValueError) as error:
            if attempt < 3:
                time.sleep(10 * (attempt + 1))
                continue
            return {'status': 'retry_needed', 'query': query, 'page': page,
                    'error': type(error).__name__, 'works': []}

def fetch_europe_pmc(query, page, timeout=30):
    """Independent public literature endpoint; no OpenAlex credentials required."""
    params = urllib.parse.urlencode({
        'query': query, 'format': 'json', 'pageSize': 100, 'page': page,
        'resultType': 'core',
    })
    url = 'https://www.ebi.ac.uk/europepmc/webservices/rest/search?' + params
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'GeobukbapResearch/0.3 (literature discovery)',
            'Accept': 'application/json'})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            data = json.load(response)
        works = []
        for item in data.get('resultList', {}).get('result', []):
            doi = item.get('doi')
            works.append({
                'title': item.get('title'),
                'doi': 'https://doi.org/' + doi if doi else None,
                'id': 'https://europepmc.org/article/' +
                      str(item.get('source', 'MED')) + '/' + str(item.get('id', '')),
                'publication_year': item.get('pubYear'),
            })
        return {'status': 'searched', 'query': query, 'page': page,
                'source': 'europe_pmc', 'works': works}
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError) as error:
        return {'status': 'retry_needed', 'query': query, 'page': page,
                'source': 'europe_pmc', 'error': type(error).__name__,
                'works': []}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pages', type=int, default=5)
    parser.add_argument('--delay', type=float, default=2.0)
    parser.add_argument('--output', type=Path, default=ROOT / 'data/research/openalex-broad-pages.jsonl')
    args = parser.parse_args()
    if not 1 <= args.pages <= 20 or args.delay < 1:
        parser.error('--pages must be 1..20 and --delay >= 1')
    names = catalog_names()
    pattern = re.compile(r'(?<![A-Za-z])(?:' + '|'.join(re.escape(n) for n in names) + r')(?![A-Za-z])', re.I)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if args.output.exists():
        with args.output.open(encoding='utf-8') as stream:
            for line in stream:
                try:
                    row = json.loads(line)
                    if row.get('status') == 'searched':
                        done.add((row['query'], row['page']))
                except (ValueError, KeyError):
                    continue
    with args.output.open('a', encoding='utf-8') as stream:
        for query in QUERIES:
            for page in range(1, args.pages + 1):
                if (query, page) in done:
                    continue
                result = fetch_page(query, page)
                if result['status'] != 'searched':
                    original_error = result.get('error')
                    result = fetch_europe_pmc(query, page)
                    if result['status'] != 'searched':
                        result['openalex_error'] = original_error
                leads = []
                for work in result.pop('works', []):
                    title = work.get('title') or ''
                    matched = sorted({m.group(0) for m in pattern.finditer(title)}, key=str.casefold)
                    if matched:
                        leads.append({'matched_title_names': matched,
                                      'title': title, 'openalex_id': work.get('id'),
                                      'doi': work.get('doi'), 'year': work.get('publication_year'),
                                      'status': 'title_match_unreviewed'})
                result['matched_title_leads'] = leads
                result['retrieved_works'] = len(leads)
                result['match_scope'] = 'title_only_unreviewed'
                stream.write(json.dumps(result, ensure_ascii=False) + '\n')
                stream.flush()
                print(json.dumps({'query': query, 'page': page, 'status': result['status'],
                                  'title_matches': len(leads)}, ensure_ascii=False), flush=True)
                time.sleep(args.delay)
if __name__ == '__main__':
    main()
