import json
from pathlib import Path

p = Path('data/academic_evidence_registry_v56.json')
data = json.loads(p.read_text(encoding='utf-8'))
assert data.get('feeding_verdict_use') is False
sources = {s['source_id']: s for s in data['sources']}

required = {
    'liesegang_hermanni_mineral_digestibility_2007': ('17988349', 'Testudo hermanni'),
    'eatwell_testudo_calcium_phosphorus_2010': ('20630020', 'Testudo graeca ibera'),
}
for sid, (pmid, taxon_text) in required.items():
    s = sources[sid]
    assert s.get('pmid') == pmid
    assert s.get('doi', '').startswith('10.')
    assert taxon_text in s.get('taxon_scope', '')
    blocked = ' | '.join(s.get('does_not_support', [])).lower()
    assert 'plant-specific' in blocked

liesegang = sources['liesegang_hermanni_mineral_digestibility_2007']
assert 'Testudo graeca ibera' not in liesegang['taxon_scope']
assert 'controlled' in liesegang['study_type'].lower()
assert any('universal captive prescription' in x for x in liesegang['does_not_support'])

eatwell = sources['eatwell_testudo_calcium_phosphorus_2010']
assert 'clinical blood-chemistry' in eatwell['study_type']
assert any(x == 'feeding trial' for x in eatwell['does_not_support'])
assert any('Ibera-specific dietary calcium requirement' in x for x in eatwell['does_not_support'])

# Critical inference boundary: an Ibera-containing sample is not direct Ibera feeding evidence.
assert 'plant_signals' not in eatwell
assert 'plant_scope' not in eatwell

print('academic physiology scope v5.6: OK')
