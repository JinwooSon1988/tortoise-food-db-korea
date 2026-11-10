#!/usr/bin/env python3
"""Read-only title triage; never infers feeding safety."""
import argparse
import html
import json
import re
from pathlib import Path

NON_TARGET = re.compile(r'\b(?:tortoise[- ]beetles?|tortoise[- ]eating|predat(?:or|ion)|golden eagles?|peer review|preprints?)\b', re.I)
ECOLOGY = re.compile(r'\b(?:diet|diets|dietary preference|foraging|feeding behaviour|feeding behavior|mycophagy|feeding preferences|grazing)\b', re.I)
TAXON = re.compile(r'\b(?:Testudo|Gopherus|Chelonoidis|Kinixys|Psammobates|Manouria|Geochelone|Stigmochelys|Centrochelys|Aldabrachelys|Astrochelys|Indotestudo|Pyxis|Homopus|Chersina|Malacochersus|Aldabran giant tortoise|tortoises?)\b', re.I)

def normalize_title(title):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]*>', ' ', html.unescape(title or ''))).strip()

def triage(payload):
    groups = {'priority_review': [], 'context_review': [], 'exclude_from_feeding_review': []}
    seen = set()
    for item in payload.get('records', []):
        title = normalize_title(item.get('title'))
        key = re.sub(r'\W+', ' ', title.casefold()).strip()
        if key in seen:
            continue
        seen.add(key)
        if NON_TARGET.search(title) or not TAXON.search(title):
            category, reason = 'exclude_from_feeding_review', 'non-target or derivative publication'
        elif ECOLOGY.search(title):
            category, reason = 'priority_review', 'tortoise diet/feeding title cue; full text unreviewed'
        else:
            category, reason = 'context_review', 'tortoise title without direct diet cue'
        groups[category].append({'title': title, 'doi': item.get('doi'),
            'source_key': item.get('source_key'), 'reason': reason,
            'abstract': normalize_title(item.get('abstract'))[:20000],
            'feeding_safety_status': 'unassessed', 'verified_plant_links': []})
    return {'input_records': len(payload.get('records', [])),
            'deduplicated_titles': len(seen),
            'counts': {k: len(v) for k,v in groups.items()}, 'groups': groups,
            'note': 'Title-only routing. No species/plant/part feeding evidence verified.'}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    output = triage(json.loads(Path(args.input).read_text(encoding='utf-8')))
    Path(args.output).write_text(json.dumps(output, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    print(output['counts'])

if __name__ == '__main__':
    main()
