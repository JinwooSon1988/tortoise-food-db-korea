import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
js=(root/'plant-detail-v56.js').read_text(encoding='utf-8')
css=(root/'plant-detail-v56.css').read_text(encoding='utf-8')
inj=(root/'scripts/inject_plant_detail_v56.py').read_text(encoding='utf-8')
pages=list((root/'plant').glob('*/index.html'))
assert len(pages)==69, len(pages)
for x in ['국명','영명','학명','과명','적용 대상','근거 등급','판정 보류','급여하지 않음','검증된 이미지 준비 중','사진과 유통명만으로 식물 종을 확정하지 않는다.']:
    assert x in js,x
assert 'verified_plant_images_v56.json' in js
assert 'exact_species' in js
# Evidence-only architecture: retired recommendation/recording routes must never
# be reintroduced into the shared plant-detail enhancer.
for retired in ['today/','meal/?add=','그래서 오늘 뭐 먹이지?','이 먹이 급여기록에 추가']:
    assert retired not in js, retired
assert "glob('*/index.html')" in inj
assert '@media(max-width:620px)' in css
registry=json.loads((root/'data/verified_plant_images_v56.json').read_text(encoding='utf-8'))
plants=json.loads((root/'data/plants.json').read_text(encoding='utf-8'))
master={p['id']:p for p in plants}
required=set(registry['policy']['required_fields'])
seen=set()
for image in registry['images']:
    pid=image['plant_id']
    assert required <= set(image), (pid, required-set(image))
    assert pid not in seen, pid
    seen.add(pid)
    assert pid in master, pid
    assert image['identity_scope'] in {'exact_species','exact_subspecies','exact_variety'}, pid
    assert 'spp.' not in master[pid]['scientific'], pid
    assert image['scientific']==master[pid]['scientific'], (pid,image['scientific'],master[pid]['scientific'])
    assert image['source_url'].startswith('https://commons.wikimedia.org/wiki/File:'), pid
    assert image['image_url'].startswith('https://commons.wikimedia.org/wiki/Special:Redirect/file/'), pid
    assert image['license'], pid
    assert image['creator'], pid
print(f'plant detail v5.6 evidence-only enhancer audit OK for 69 pages; {len(seen)} verified images')
