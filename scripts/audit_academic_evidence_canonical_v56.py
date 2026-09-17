from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = json.loads((ROOT / 'data/academic_evidence_registry_v56.json').read_text(encoding='utf-8'))
MATRIX = json.loads((ROOT / 'data/evidence_matrix_v56.json').read_text(encoding='utf-8'))

assert REGISTRY.get('feeding_verdict_use') is False, 'academic registry must not set feeding verdicts'

sources = REGISTRY.get('sources', [])
source_ids = [s.get('source_id') for s in sources]
assert len(source_ids) == len(set(source_ids)), 'duplicate academic source_id'
assert all(source_ids), 'academic source_id is required'

for source in sources:
    assert source.get('supports'), f"{source.get('source_id')}: supports required"
    assert source.get('does_not_support'), f"{source.get('source_id')}: does_not_support required"

anchors = MATRIX.get('source_anchors', {})
foods = MATRIX.get('foods', [])
food_ids = [f.get('food_id') for f in foods]
assert len(food_ids) == len(set(food_ids)), 'duplicate food_id in canonical evidence matrix'

# Direct Ibera evidence already promoted into the canonical matrix must point to a
# registered academic source and preserve its inference boundary.
for food in foods:
    for evidence in food.get('direct_evidence', []):
        source_id = evidence.get('source_id')
        assert source_id in source_ids, f"{food.get('food_id')}: unregistered direct source {source_id}"
        assert source_id in anchors, f"{food.get('food_id')}: direct source missing canonical anchor {source_id}"
        assert evidence.get('taxon_scope'), f"{food.get('food_id')}: taxon_scope required"
        assert evidence.get('identity_scope'), f"{food.get('food_id')}: identity_scope required"

# The strongest current Ibera plant signals must remain canonicalized. These are
# genus-level where the primary paper is genus-level; this test intentionally
# prevents later code from silently upgrading them to species-level proof.
required = {
    'dandelion': ('iftime_ibera_dobrogea_2012', 'genus'),
    'sowthistle': ('iftime_ibera_dobrogea_2012', 'genus'),
    'clover': ('iftime_ibera_dobrogea_2012', 'genus'),
    'alfalfa': ('iftime_ibera_dobrogea_2012', 'genus'),
    'chicory': ('mitrevichin_ibera_bulgaria_2023', 'exact_species'),
}
by_food = {f['food_id']: f for f in foods}
for food_id, (source_id, identity_scope) in required.items():
    assert food_id in by_food, f'{food_id}: missing canonical food row'
    matches = [e for e in by_food[food_id].get('direct_evidence', []) if e.get('source_id') == source_id]
    assert matches, f'{food_id}: required direct Ibera source missing'
    assert any(e.get('identity_scope') == identity_scope for e in matches), f'{food_id}: identity scope drift'

# Clinical Lactuca virosa case must never be generalized to lettuce/romaine.
virosa = next(s for s in sources if s.get('source_id') == 'lactuca_virosa_fmt_case_2025')
limits = ' '.join(virosa.get('does_not_support', []))
assert virosa.get('causality_status') == 'unconfirmed', 'Lactuca virosa causality must remain unconfirmed'
assert 'Lactuca sativa' in limits and 'entire Lactuca genus' in limits, 'Lactuca inference boundary missing'

# Composition evidence and academic evidence remain descriptive inputs; this
# file must not grow prescription-like fields.
forbidden = {'feeding_frequency', 'feeding_percentage', 'daily_allowance', 'unlimited', 'evidence_grade_override', 'feeding_verdict'}
def walk(value, path='root'):
    if isinstance(value, dict):
        for key, child in value.items():
            assert key not in forbidden, f'forbidden prescriptive field {path}.{key}'
            walk(child, f'{path}.{key}')
    elif isinstance(value, list):
        for i, child in enumerate(value):
            walk(child, f'{path}[{i}]')
walk(REGISTRY, 'registry')
walk(MATRIX, 'matrix')

print(f'Academic canonical evidence audit PASS: {len(sources)} sources, {len(foods)} canonical food rows')
