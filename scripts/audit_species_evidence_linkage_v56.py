from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
LINKAGE_PATH = ROOT / 'data/species_evidence_linkage_v56.json'
MATRIX_PATH = ROOT / 'data/evidence_matrix_v56.json'

linkage = json.loads(LINKAGE_PATH.read_text(encoding='utf-8'))
matrix = json.loads(MATRIX_PATH.read_text(encoding='utf-8'))

assert linkage.get('schema_version') == '5.6', 'linkage schema must remain v5.6'
links = linkage.get('links', [])
assert links, 'species evidence linkage must contain links'

food_rows = {row.get('food_id'): row for row in matrix.get('foods', [])}
assert all(food_rows), 'canonical evidence matrix food_id required'

food_ids = [item.get('food_id') for item in links]
assert len(food_ids) == len(set(food_ids)), 'duplicate food_id in species evidence linkage'

required_fields = {
    'food_id', 'canonical_taxon', 'asset', 'canonical_matrix_status',
    'strongest_applicability', 'exact_ibera_gap', 'public_detail_rule'
}
for item in links:
    food_id = item.get('food_id')
    missing = sorted(required_fields - set(item))
    assert not missing, f'{food_id}: missing linkage fields {missing}'
    assert food_id in food_rows, f'{food_id}: canonical food row does not exist'

    asset = ROOT / item['asset']
    assert asset.is_file(), f'{food_id}: linked species evidence asset missing: {item["asset"]}'
    payload = json.loads(asset.read_text(encoding='utf-8'))
    master = payload.get('canonical_master', {})
    assert master.get('id') == food_id, f'{food_id}: asset canonical master id mismatch'
    assert master.get('scientific_name') == item['canonical_taxon'], f'{food_id}: canonical taxon drift between linkage and asset'
    assert payload.get('records'), f'{food_id}: linked species evidence asset has no records'

    for text_field in ('strongest_applicability', 'exact_ibera_gap', 'public_detail_rule'):
        value = item.get(text_field)
        assert isinstance(value, str) and value.strip(), f'{food_id}: {text_field} must be non-empty text'

# The linkage layer is descriptive evidence plumbing only. It must never become
# a back door for feeding prescriptions or verdict overrides.
forbidden_keys = {
    'feeding_level', 'diet_role', 'evidence_grade', 'feeding_verdict',
    'feeding_frequency', 'feeding_percentage', 'daily_allowance',
    'weekly_frequency', 'staple', 'unlimited', 'verdict_override'
}
def walk(value, path='linkage'):
    if isinstance(value, dict):
        for key, child in value.items():
            assert key not in forbidden_keys, f'forbidden verdict/prescription field {path}.{key}'
            walk(child, f'{path}.{key}')
    elif isinstance(value, list):
        for index, child in enumerate(value):
            walk(child, f'{path}[{index}]')
walk(linkage)

qa = linkage.get('qa_requirements', {})
for key in ('no_orphan_asset', 'no_missing_asset', 'public_traceability', 'verdict_independence'):
    assert qa.get(key), f'missing declared QA requirement: {key}'

expected = {'plantain', 'dandelion', 'sowthistle', 'clover', 'alfalfa'}
assert expected <= set(food_ids), f'missing current species-resolved linkage foods: {sorted(expected - set(food_ids))}'

print(f'Species evidence linkage audit PASS: {len(links)} canonical links verified')
