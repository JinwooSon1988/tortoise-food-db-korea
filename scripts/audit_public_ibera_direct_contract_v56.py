import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
obj=json.loads((root/'data/public_ibera_direct_evidence_contract_v56.json').read_text(encoding='utf-8'))
assert obj['version']=='5.6'
assert obj['feeding_verdict_use'] is False
assert obj['display_only_when_mapped_plant_id'] is True
assert obj['identity_labels']['exact_species'] != obj['identity_labels']['genus']
for key in ['captive_feeding_percentage','daily_feeding','unlimited_safety','genus_to_exact_species_promotion']:
    assert key in obj['forbidden_inferences']
for key in ['feeding_verdict','evidence_grade','feeding_frequency','diet_percentage']:
    assert key in obj['does_not_change']
print('OK: public Ibera direct evidence contract')
