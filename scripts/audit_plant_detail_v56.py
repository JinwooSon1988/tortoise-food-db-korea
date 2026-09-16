from pathlib import Path
root=Path(__file__).resolve().parents[1]
js=(root/'plant-detail-v56.js').read_text(encoding='utf-8')
css=(root/'plant-detail-v56.css').read_text(encoding='utf-8')
inj=(root/'scripts/inject_plant_detail_v56.py').read_text(encoding='utf-8')
pages=list((root/'plant').glob('*/index.html'))
assert len(pages)==69, len(pages)
for x in ['국명','영명','학명','과명','적용 대상','근거 등급','판정 보류','급여하지 않음','검증된 이미지 준비 중','사진과 유통명만으로 식물 종을 확정하지 않는다.']:
    assert x in js,x
assert 'glob(\'*/index.html\')' in inj
assert '@media(max-width:620px)' in css
print('plant detail v5.6 enhancer audit OK for 69 pages')
