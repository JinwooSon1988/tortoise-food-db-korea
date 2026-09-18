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

def asset_identity(payload):
    """Normalize historical v5.6 research envelopes without rewriting evidence."""
    master = payload.get('canonical_master')
    if isinstance(master, dict):
        food_id = master.get('id') or master.get('key')
        taxon = master.get('scientific_name')
        records = payload.get('records')
        if records is None:
            records = payload.get('evidence_records')
        return food_id, taxon, records

    plant_master = payload.get('plant_master')
    if isinstance(plant_master, dict):
        return (
            plant_master.get('id') or plant_master.get('key'),
            plant_master.get('scientific_name'),
            payload.get('records') or payload.get('evidence_records')
        )
    if isinstance(plant_master, str):
        # Trifolium-era envelope: the master string itself is the canonical taxon.
        # food_id is intentionally resolved from the linkage item below because
        # this historical asset never stored the canonical key.
        return None, plant_master, payload.get('records') or payload.get('evidence_records')

    # Legacy Plantago/Taraxacum-style envelope.
    return (
        payload.get('food_id'),
        payload.get('canonical_master_taxon'),
        payload.get('evidence') or payload.get('records') or payload.get('evidence_records')
    )

for item in links:
    food_id = item.get('food_id')
    missing = sorted(required_fields - set(item))
    assert not missing, f'{food_id}: missing linkage fields {missing}'
    assert food_id in food_rows, f'{food_id}: canonical food row does not exist'

    asset = ROOT / item['asset']
    assert asset.is_file(), f'{food_id}: linked species evidence asset missing: {item["asset"]}'
    payload = json.loads(asset.read_text(encoding='utf-8'))
    asset_food_id, asset_taxon, records = asset_identity(payload)
    if asset_food_id is not None:
        assert asset_food_id == food_id, f'{food_id}: asset canonical food id mismatch'
    assert asset_taxon == item['canonical_taxon'], f'{food_id}: canonical taxon drift between linkage and asset'
    assert isinstance(records, list) and records, f'{food_id}: linked species evidence asset has no records/evidence'

    for text_field in ('strongest_applicability', 'exact_ibera_gap', 'public_detail_rule'):
        value = item.get(text_field)
        assert isinstance(value, str) and value.strip(), f'{food_id}: {text_field} must be non-empty text'

# Descriptive evidence plumbing only: never permit verdict/prescription overrides.
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

# Every current species-resolved v5.6 research asset must be registered.
registered_assets = {item['asset'] for item in links}
species_assets = {
    str(path.relative_to(ROOT)).replace('\\', '/')
    for path in (ROOT / 'data').glob('*_species_evidence_v56.json')
}
assert species_assets <= registered_assets, (
    'orphan species evidence assets: ' + ', '.join(sorted(species_assets - registered_assets))
)

print(f'Species evidence linkage audit PASS: {len(links)} canonical links verified; '
      f'{len(species_assets)} species evidence assets registered')
