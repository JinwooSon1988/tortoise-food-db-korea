#!/usr/bin/env python3
"""Build a site-ready unreviewed literature index from checkpointed OpenAlex JSONL.

Run after the crawler. Does NOT change feeding grades or verified evidence.
"""
import argparse
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def build(input_path, existing_path):
    base = json.loads(existing_path.read_text(encoding='utf-8'))
    taxa = base.setdefault('taxa', {})
    by_name = {}
    for path in sorted((ROOT / 'data/plant-catalog').glob('taxa-??.json')):
        for plant in json.loads(path.read_text(encoding='utf-8'))['records']:
            name = plant.get('scientific', '').strip().casefold()
            if name:
                by_name.setdefault(name, set()).add(plant['id'])
    latest = {}
    with input_path.open(encoding='utf-8') as stream:
        for line in stream:
            try:
                row = json.loads(line)
                name = row['name'].strip().casefold()
                if row.get('status') == 'searched' or name not in latest:
                    latest[name] = row
            except (ValueError, KeyError, TypeError):
                continue
    stats = defaultdict(int)
    for name, row in latest.items():
        if row.get('status') != 'searched':
            stats['retry_needed'] += 1
            continue
        ids = by_name.get(name, ())
        if len(ids) != 1:
            stats['unmatched_or_ambiguous'] += 1
            continue
        taxon_id = next(iter(ids))
        target = taxa.setdefault(taxon_id, {'literature_leads': [], 'community_mentions': []})
        leads = target.setdefault('literature_leads', [])
        seen = {(str(x.get('url') or '').casefold(), str(x.get('title') or '').casefold())
                for x in leads}
        for hit in row.get('hits') or []:
            title = (hit.get('title') or '').strip()
            # 'Tortoise beetle' is an insect, not a tortoise feeding record.
            if 'tortoise beetle' in title.casefold():
                stats['excluded_tortoise_beetle_false_positives'] += 1
                continue
            url = hit.get('doi') or hit.get('source_url') or hit.get('openalex_id')
            if not title or not isinstance(url, str) or not url.startswith('https://'):
                continue
            key = (url.casefold(), title.casefold())
            if key in seen:
                stats['duplicate_leads'] += 1
                continue
            leads.append({'title': title, 'year': str(hit.get('year') or ''),
                          'url': url, 'verification': 'search_hit_unreviewed',
                          'feeding_safety_status': 'unassessed'})
            seen.add(key)
            stats['new_unreviewed_leads'] += 1
        stats['matched_taxa'] += 1
    # A valid no-op replay must report zero additions rather than omit the metric.
    stats.setdefault('new_unreviewed_leads', 0)
    base['warning'] = 'Search leads only; not evidence of consumption or feeding safety.'
    return base, dict(stats)

def main():
    p = argparse.ArgumentParser()
    p.add_argument('input', type=Path)
    p.add_argument('--existing', type=Path,
                   default=ROOT / 'data/research_source_leads_index.json')
    p.add_argument('--output', type=Path,
                   default=ROOT / 'data/research_source_leads_index.json')
    args = p.parse_args()
    result, stats = build(args.input, args.existing)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False,
                                      separators=(',', ':')) + '\n', encoding='utf-8')
    print(json.dumps(stats, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
