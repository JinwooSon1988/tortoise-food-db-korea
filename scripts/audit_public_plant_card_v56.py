from pathlib import Path
import json
root=Path(__file__).resolve().parents[1]
contract=json.loads((root/'data/public_plant_card_contract_v56.json').read_text(encoding='utf-8'))
js=(root/'public-plant-card-v56.js').read_text(encoding='utf-8')
css=(root/'public-plant-card-v56.css').read_text(encoding='utf-8')
assert contract['scope'].startswith('All 69 master foods')
for token in ['영명','학명','과명','급여하지 않음','판정 보류','적용 대상','근거 등급','검증된 이미지 준비 중','사진과 유통명만으로 식물 종을 확정하지 않는다.']:
    assert token in js, token
for verdict in contract['feeding_display']['public_levels']:
    if verdict!='blocked_or_unresolved': assert verdict in js, verdict
assert '.public-v56' in css and '@media(max-width:620px)' in css
print('public plant card v5.6 contract/render audit OK')
