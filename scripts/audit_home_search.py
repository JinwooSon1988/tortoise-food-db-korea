import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
html = (root / 'index.html').read_text(encoding='utf-8')
plants = json.loads((root / 'data' / 'plants.json').read_text(encoding='utf-8'))
base = json.loads((root / 'data' / 'assessments.json').read_text(encoding='utf-8'))
addenda = []
for i in range(1, 13):
    name = 'assessments_korea_addendum.json' if i == 1 else f'assessments_korea_addendum_{i}.json'
    addenda += json.loads((root / 'data' / name).read_text(encoding='utf-8'))
assessments = base + addenda

assert len(plants) == 69, len(plants)
assert "현재 등록된 '+plants.length+'종" in html
assert "상세 근거 보기 →" in html
assert "오늘 식단 후보 보기" in html
assert "<b>적용 범위</b> · " in html
assert "do_not_feed:'급여 비권장'" in html
assert "v5.3" in html
for i in range(1, 13):
    name = 'assessments_korea_addendum.json' if i == 1 else f'assessments_korea_addendum_{i}.json'
    assert name in html, name

ids = {p['id'] for p in plants}
assessment_ids = {a['plant_id'] for a in assessments}
for pid in ('chicory','chard','lambs_lettuce'):
    assert pid in ids
    assert pid in assessment_ids
    assert (root / 'plant' / pid / 'index.html').exists()

print('public home search audit: PASS')
