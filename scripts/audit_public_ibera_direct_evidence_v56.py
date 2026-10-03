import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
gen=(ROOT/'scripts/generate_static_pages.py').read_text(encoding='utf-8')
data=json.loads((ROOT/'data/ibera_direct_feeding_evidence_v56.json').read_text(encoding='utf-8'))
assert 'ibera_direct_feeding_evidence_v56.json' in gen
assert '이베라 야생 직접 관찰' in gen
assert '사육 급여 비율·매일 급여·무제한 안전성을 뜻하지 않는다' in gen
assert 'identity_scope")=="exact_species"' in gen
assert '속 수준 관찰' in gen and '원 연구 확인' in gen
checked=0
for o in data['observations']:
    page=ROOT/'plant'/str(o.get('plant_id'))/'index.html'
    if not o.get('plant_id') or not page.exists():
        continue
    text=page.read_text(encoding='utf-8')
    assert 'data-ibera-direct' in text, o['plant_id']
    if o.get('identity_scope')!='exact_species':
        assert '속 수준 관찰' in text, o['plant_id']
    checked+=1
assert not (ROOT/'ibera-direct-evidence-v56.js').exists(), 'runtime enhancer retired; observations render statically'
print(f'OK: direct-Ibera wild observations rendered statically for {checked} observations')
