#!/usr/bin/env python3
import json, math, re, sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
NUTRITION = ROOT / 'data' / 'plant_nutrition_v56.json'
PLANTS = ROOT / 'data' / 'plants.json'

FORBIDDEN_KEYS = {
    'verdict', 'feeding_verdict', 'feeding_level', 'frequency', 'feeding_frequency',
    'safe', 'safety', 'recommendation', 'recommended_ratio', 'diet_ratio'
}
NUMERIC_SUFFIXES = ('_g', '_mg', '_mcg')
DATA_TYPES = {'SR Legacy', 'Foundation'}
VERIFICATION_STATUSES = {'source_listed', 'verified'}


def fail(msg):
    print(f'ERROR: {msg}')
    return 1


def main():
    errors = []
    data = json.loads(NUTRITION.read_text(encoding='utf-8'))
    plants = json.loads(PLANTS.read_text(encoding='utf-8'))
    master = {p.get('id'): p for p in plants}

    if str(data.get('schema_version')) != '5.6': errors.append('schema_version must be 5.6')
    policy = data.get('policy') or {}
    if policy.get('purpose') != 'descriptive_composition_only': errors.append('policy.purpose must be descriptive_composition_only')
    if policy.get('feeding_verdict_use') is not False: errors.append('policy.feeding_verdict_use must be exactly false')
    if not policy.get('verification_policy'): errors.append('policy.verification_policy is required')

    seen = set()
    required = ('plant_id','food_description','source_name','source_id','source_url','data_type','verification_status','basis')
    for i, n in enumerate(data.get('plants') or []):
        tag = n.get('plant_id') or f'row#{i}'
        for key in required:
            if not n.get(key): errors.append(f'{tag}: missing {key}')
        pid = n.get('plant_id')
        if pid in seen: errors.append(f'{tag}: duplicate plant_id')
        seen.add(pid)
        p = master.get(pid)
        if not p: errors.append(f'{tag}: no matching master plant')
        else:
            sci = str(p.get('scientific') or '').strip(); status = str(p.get('identity_status') or '').lower()
            if re.search(r'\bspp\.?$', sci, re.I): errors.append(f'{tag}: genus-level spp. identity cannot receive species/food nutrition mapping ({sci})')
            if any(x in status for x in ('blocked','unverified','needs_')): errors.append(f'{tag}: unresolved master identity_status={status}')

        if n.get('source_name') != 'USDA FoodData Central': errors.append(f'{tag}: source_name must be USDA FoodData Central')
        m = re.fullmatch(r'FDC\s+(\d+)', str(n.get('source_id') or ''))
        if not m: errors.append(f'{tag}: invalid source_id format')
        try:
            u = urlparse(str(n.get('source_url') or ''))
            if u.scheme != 'https' or u.hostname != 'fdc.nal.usda.gov': errors.append(f'{tag}: source_url must use https://fdc.nal.usda.gov')
            if m and f'/food-details/{m.group(1)}/' not in u.path: errors.append(f'{tag}: source URL FDC id does not match source_id')
        except Exception: errors.append(f'{tag}: invalid source_url')

        if n.get('data_type') not in DATA_TYPES: errors.append(f'{tag}: data_type must be one of {sorted(DATA_TYPES)}')
        verification = n.get('verification_status')
        if verification not in VERIFICATION_STATUSES: errors.append(f'{tag}: invalid verification_status')
        verified_at = n.get('verified_at')
        if verification == 'verified':
            if not isinstance(verified_at, str): errors.append(f'{tag}: verified record requires verified_at YYYY-MM-DD')
            else:
                try: date.fromisoformat(verified_at)
                except ValueError: errors.append(f'{tag}: invalid verified_at date')
        elif verified_at is not None:
            errors.append(f'{tag}: source_listed record must keep verified_at null')

        for key in n:
            if key.lower() in FORBIDDEN_KEYS: errors.append(f'{tag}: forbidden feeding-decision field {key}')
        for key, value in n.items():
            if key.endswith(NUMERIC_SUFFIXES) or key == 'calcium_phosphorus_ratio':
                if isinstance(value, bool) or not isinstance(value, (int,float)) or not math.isfinite(value) or value < 0:
                    errors.append(f'{tag}: {key} must be finite non-negative number')

        ca, ph, ratio = n.get('calcium_mg'), n.get('phosphorus_mg'), n.get('calcium_phosphorus_ratio')
        if ratio is not None:
            if not isinstance(ca,(int,float)) or not isinstance(ph,(int,float)) or ca <= 0 or ph <= 0: errors.append(f'{tag}: positive calcium/phosphorus required for Ca:P')
            elif abs((ca/ph)-ratio) > 0.02: errors.append(f'{tag}: Ca:P {ratio} does not match calcium/phosphorus ({ca/ph:.4f})')

    if errors:
        for e in errors: fail(e)
        print(f'Nutrition v5.6 integrity audit FAILED: {len(errors)} error(s)'); return 1
    print(f'Nutrition v5.6 integrity audit OK: {len(seen)} plant record(s)'); return 0

if __name__ == '__main__': sys.exit(main())
