import json
import re
from pathlib import Path

root = Path(__file__).resolve().parents[1]
js = (root / 'fresh-primary-combo-explain.js').read_text(encoding='utf-8')
sw = (root / 'sw.js').read_text(encoding='utf-8')
data = json.loads((root / 'data' / 'wild_observation_frequency.json').read_text(encoding='utf-8'))

expected = {
    ('dandelion', 'iftime_ibera_dobrogea_2012'): ('Moderate', '5–10%'),
    ('sowthistle', 'iftime_ibera_dobrogea_2012'): ('Low', '1–5%'),
    ('clover', 'iftime_ibera_dobrogea_2012'): ('High', '>10%'),
    ('alfalfa', 'iftime_ibera_dobrogea_2012'): ('Moderate', '5–10%'),
}
actual = {(x['plant_id'], x['source_id']): (x['frequency_class'], x['frequency_range']) for x in data}
assert actual == expected, actual

for row in data:
    note = row.get('interpretation_note', '')
    assert '사육환경의 권장 급여비율' in note or '사육 급여비율' in note
    assert row.get('taxon_reported')
    assert row.get('part_reported')

assert "wild_observation_frequency.json" in js
assert "frequencyFor(id,sourceId)" in js
assert "야생 관찰 빈도 · 급여비율 아님" in js
assert "구조화된 식물별 야생 관찰 빈도값이 없다" in js
assert "Low·Moderate·High 및 백분율 구간은 야생 관찰 빈도 분류이며 사육 급여비율이 아니다" in js
assert "frequencyHTML(id,e.id)" in js

assert "./data/wild_observation_frequency.json" in sw
m = re.search(r"const CACHE='tfd-v51-stable-(\d+)'", sw)
assert m and int(m.group(1)) >= 17

print('wild frequency label audit: PASS')
