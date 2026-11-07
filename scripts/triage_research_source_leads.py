#!/usr/bin/env python3
"""Deterministic bulk source-lead triage. Search hits NEVER imply feeding safety."""
import argparse
import html
import json
import pathlib
import re
from collections import Counter
from urllib.parse import urlsplit

TORTOISE = re.compile(r'\b(?:tortoises?|testudinidae|testudo|geochelone|centrochelys|chelonoidis|stigmochelys|astrochelys|aldabrachelys|gopherus|kinixys|homopus|psammobates|manouria|indotestudo|malacochersus|agrionemys|pyxis|chersina)\b', re.I)
FEEDING = re.compile(r'\b(?:diet|dietary|feed(?:ing|s)?|forag(?:e|ing)|graz(?:e|ing)|herbivor(?:e|y)|food|nutrition|consum(?:e|ption)|ingest(?:ion|ed)|browse|gut contents?|stomach contents?)\b', re.I)
NON_REPTILE_TORTOISE = re.compile(r'\b(?:tortoise beetles?|tortoise-shell beetles?|tortoiseshell butterflies?)\b', re.I)
PRIORITY = {'both_title_signals': 0, 'one_title_signal': 1, 'no_title_signals': 2, 'community_unassessed': 3}

def run(source, target):
    data = json.loads(pathlib.Path(source).read_text(encoding='utf-8'))
    if not isinstance(data.get('taxa'), dict):
        raise ValueError('Missing taxa mapping')
    seen, records, counts = set(), [], Counter()
    for taxon_id, groups in sorted(data['taxa'].items()):
        if not re.fullmatch(r'gbif:\d+', taxon_id) or not isinstance(groups, dict):
            raise ValueError('Invalid taxon: ' + taxon_id)
        for kind, expected in (('literature_leads', 'search_hit_unreviewed'), ('community_mentions', 'community_claim_not_independently_verified')):
            leads = groups.get(kind, [])
            if not isinstance(leads, list):
                raise ValueError('Invalid source list: ' + taxon_id)
            for lead in leads:
                if not isinstance(lead, dict) or lead.get('verification') != expected or lead.get('feeding_safety_status') != 'unassessed':
                    raise ValueError('Unverified lead was changed into a verdict: ' + taxon_id)
                url = lead.get('url') if kind == 'literature_leads' else lead.get('source_url')
                if not isinstance(url, str) or not (urlsplit(url).scheme == 'https' and urlsplit(url).hostname):
                    raise ValueError('Invalid HTTPS source: ' + taxon_id)
                key = (taxon_id, kind, url.casefold())
                if key in seen:
                    counts['duplicate_pairs_removed'] += 1
                    continue
                seen.add(key)
                title = html.unescape(re.sub(r'<[^>]*>', ' ', str(lead.get('title') or ''))).strip()
                if kind == 'community_mentions':
                    priority = 'community_unassessed'
                else:
                    signals = int(bool(TORTOISE.search(title)) and not bool(NON_REPTILE_TORTOISE.search(title))) + int(bool(FEEDING.search(title)))
                    priority = ('no_title_signals', 'one_title_signal', 'both_title_signals')[signals]
                counts[priority] += 1
                records.append({'taxon_id': taxon_id, 'kind': kind, 'source_url': url, 'title': title, 'priority': priority,
                                'verification': expected, 'feeding_safety_status': 'unassessed', 'feeding_claim_verified': False})
    records.sort(key=lambda r: (PRIORITY[r['priority']], r['taxon_id'], r['kind'], r['source_url']))
    result = {'schema_version': '1.0', 'method': 'title_keyword_screen_only',
              'warning': 'No feeding claims or safety grades verified. Review original sources, plant parts and tortoise species.',
              'counts': dict(sorted(counts.items())), 'records': records}
    out = pathlib.Path(target)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'unique_pairs': len(records), 'counts': result['counts']}, ensure_ascii=False))

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--index', default='data/research_source_leads_index.json')
    p.add_argument('--out', default='data/research_leads_triaged.json')
    a = p.parse_args()
    run(a.index, a.out)
