#!/usr/bin/env python3
"""Prioritize verified tortoise feeding records, without inferring safety."""
import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERIFIED = {'full_text_verified', 'review_full_text_verified',
            'guideline_full_text_verified'}
POSITIVE = {'wild_feeding_observation', 'captive_feeding_record',
            'husbandry_recommendation'}
NEGATIVE = {'wild_diet_not_detected', 'offered_not_eaten'}
def main():
    p = argparse.ArgumentParser()
    p.add_argument('--corpus', type=Path,
                   default=ROOT / 'data/catalog-evidence/batch-002-20261021.json')
    p.add_argument('--output', type=Path,
                   default=ROOT / 'data/catalog-evidence/batch-002-priority-audit.json')
    args = p.parse_args()
    data = json.loads(args.corpus.read_text(encoding='utf-8'))
    by_name = defaultdict(list)
    for record in data['records']:
        name = record.get('reported_name', '').strip()
        if name:
            by_name[name.casefold()].append(record)
    ranked = []
    for key, records in by_name.items():
        verified = [r for r in records if r.get('verification') in VERIFIED]
        feeding = [r for r in verified if r.get('type') in POSITIVE]
        negative = [r for r in verified if r.get('type') in NEGATIVE]
        sources = sorted({r['source_key'] for r in verified})
        ranked.append({
            'reported_name': records[0]['reported_name'],
            'verified_positive_records': len(feeding),
            'verified_negative_records': len(negative),
            'verified_source_count': len(sources),
            'verified_tortoise_taxa': sorted({r['tortoise'] for r in verified}),
            'unverified_records': len(records) - len(verified),
            'feeding_safety_status': 'unassessed',
        })
    ranked.sort(key=lambda r: (-r['verified_positive_records'],
                               -r['verified_source_count'], r['reported_name'].casefold()))
    result = {
        'scope': 'Batch 002 source reported names, not confirmed unique GBIF catalog taxa',
        'caution': 'Consumption records do not establish feeding safety; negative records must not be counted as feeding evidence.',
        'total_records': len(data['records']),
        'distinct_reported_names': len(by_name),
        'names_with_verified_positive_feeding_or_husbandry': sum(r['verified_positive_records'] > 0 for r in ranked),
        'names_with_verified_negative_only': sum(r['verified_negative_records'] > 0 and r['verified_positive_records'] == 0 for r in ranked),
        'names_without_verified_positive_or_negative': sum(r['verified_positive_records'] == 0 and r['verified_negative_records'] == 0 for r in ranked),
        'records_by_type': dict(Counter(r.get('type') for r in data['records'])),
        'priority_names': ranked,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k != 'priority_names'}, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
