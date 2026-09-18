import json
import re
from pathlib import Path

root = Path(__file__).resolve().parents[1]
js = (root / 'fresh-primary-combo-explain.js').read_text(encoding='utf-8')
data = json.loads((root / 'data' / 'wild_observation_frequency.json').read_text(encoding='utf-8'))

# Iftime & Iftime (2012) supports qualitative preference/predilection for
# Taraxacum, Sonchus, Trifolium and Medicago. It does not support the former
# plant-specific Low/Moderate/High percentage bins. Keep those invented bins
# out of the structured frequency asset.
iftime = [x for x in data if x.get('source_id') == 'iftime_ibera_dobrogea_2012']
assert not iftime, iftime

# Regression guard: do not reintroduce the old Iftime-specific categorical
# bins in public plant pages or this structured asset. This is intentionally
# narrow; source-backed quantitative observations from other studies remain
# allowed when their population/method context is explicit.
forbidden = (
    'Low (1–5%)', 'Low (1-5%)',
    'Moderate (5–10%)', 'Moderate (5-10%)',
    'High (>10%)',
)
public_texts = []
for path in (root / 'plant').glob('*/index.html'):
    public_texts.append((str(path.relative_to(root)), path.read_text(encoding='utf-8')))
public_texts.append(('data/wild_observation_frequency.json', json.dumps(data, ensure_ascii=False)))
for path, text in public_texts:
    if 'iftime' not in text.lower():
        continue
    for label in forbidden:
        assert label not in text, f'{path}: unsupported Iftime frequency bin: {label}'

for row in data:
    note = row.get('interpretation_note', '')
    assert '사육환경의 권장 급여비율' in note or '사육 급여비율' in note
    assert row.get('taxon_reported')
    assert row.get('part_reported')

# Preserve the scientific interpretation checks. Missing structured frequency
# data must render as missing rather than being reconstructed from prose.
assert "wild_observation_frequency.json" in js
assert "frequencyFor(id,sourceId)" in js
assert "야생 관찰 빈도 · 급여비율 아님" in js
assert "구조화된 식물별 야생 관찰 빈도값이 없다" in js
assert "frequencyHTML(id,e.id)" in js

print('wild frequency label audit: PASS')
