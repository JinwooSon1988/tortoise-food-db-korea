#!/usr/bin/env python3
"""Build a source-first review queue from unverified taxon-source leads.

A paper is reviewed once, then each taxon association is verified independently.
This program makes no safety assertions and does not fetch third-party sites.
"""
import argparse
import json
import pathlib
from collections import Counter, defaultdict
from urllib.parse import urlsplit, urlunsplit

def canonical_url(url):
    parts = urlsplit(url)
    if parts.scheme.lower() != 'https' or not parts.hostname or parts.username or parts.password:
        raise ValueError('Invalid source URL: ' + str(url))
    host = parts.hostname.lower()
    path = parts.path.rstrip('/') or '/'
    if host in ('doi.org', 'dx.doi.org'):
        host = 'doi.org'
        path = '/' + path.lstrip('/').lower()
    return urlunsplit(('https', host + ((':' + str(parts.port)) if parts.port else ''), path, parts.query, ''))

def build(source):
    groups = json.loads(pathlib.Path(source).read_text(encoding='utf-8'))
    if not isinstance(groups.get('records'), list):
        raise ValueError('Expected triage records')
    by_url = defaultdict(lambda: {'taxa': set(), 'links': [], 'titles': set(), 'priority': 99})
    order = {'both_title_signals': 0, 'one_title_signal': 1, 'no_title_signals': 2}
    for row in groups['records']:
        if row.get('kind') != 'literature_leads':
            continue
        if row.get('verification') != 'search_hit_unreviewed' or row.get('feeding_safety_status') != 'unassessed' or row.get('feeding_claim_verified') is not False:
            raise ValueError('Source was improperly treated as verified')
        url = canonical_url(row['source_url'])
        item = by_url[url]
        taxon = row['taxon_id']
        if taxon in item['taxa']:
            raise ValueError('Duplicate source-taxon association: ' + url + ' ' + taxon)
        item['taxa'].add(taxon)
        item['links'].append({'taxon_id': taxon, 'association_verified': False, 'plant_part': None, 'tortoise_species': None, 'source_passage': None})
        item['titles'].add(row.get('title') or '')
        item['priority'] = min(item['priority'], order[row['priority']])
    records = []
    for url, item in by_url.items():
        records.append({'source_url': url, 'title_candidates': sorted(item['titles']), 'title_signal_priority': item['priority'],
                        'source_review_status': 'not_reviewed', 'source_type_confirmed': False,
                        'taxon_associations': sorted(item['links'], key=lambda x: x['taxon_id']),
                        'feeding_safety_status': 'unassessed'})
    records.sort(key=lambda r: (r['title_signal_priority'], -len(r['taxon_associations']), r['source_url']))
    tally = Counter(str(r['title_signal_priority']) for r in records)
    return {'schema_version': '1.0', 'warning': 'Source-first research queue, not validated feeding evidence.',
            'counts': {'unique_sources': len(records), 'source_taxon_links': sum(len(r['taxon_associations']) for r in records), 'priority_groups': dict(sorted(tally.items()))},
            'records': records}

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--input', default='data/research_leads_triaged.json')
    p.add_argument('--output', default='data/research_unique_source_review_queue.json')
    a = p.parse_args()
    result = build(a.input)
    out = pathlib.Path(a.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result['counts'], ensure_ascii=False))

if __name__ == '__main__':
    main()
