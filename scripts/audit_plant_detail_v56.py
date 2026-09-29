import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
js=(root/'plant-detail-v56.js').read_text(encoding='utf-8')
css=(root/'plant-detail-v56.css').read_text(encoding='utf-8')
inj=(root/'scripts/inject_plant_detail_v56.py').read_text(encoding='utf-8')
pages=list((root/'plant').glob('*/index.html'))
plants=json.loads((root/'data/plants.json').read_text(encoding='utf-8'))
assessments=json.loads((root/'data/public_assessments.json').read_text(encoding='utf-8'))
if isinstance(assessments,dict): assessments=assessments.get('assessments',assessments.get('records',[]))
public_groups={'Mediterranean_Testudo','Tortoise_general','Herbivorous_reptile_general'}
assessed_ids={a['plant_id'] for a in assessments if a.get('species_group') in public_groups}
public_ids={p['id'] for p in plants if p.get('identity_status')!='candidate_name' and p.get('id') in assessed_ids}
expected=len(public_ids)
page_ids={p.parent.name for p in pages}
missing=sorted(public_ids-page_ids)
assert not missing, ('missing reviewed public pages',missing)
for x in ['국명','영명','학명','과명','적용 대상','근거 등급','판정 보류','급여하지 않음','검증된 이미지 준비 중','사진과 유통명만으로 식물 종을 확정하지 않는다.']:
    assert x in js,x
assert 'verified_plant_images_v56.json' in js
assert 'exact_species' in js
generator=(root/'scripts/generate_static_pages.py').read_text(encoding='utf-8')

assert '육지거북 먹이 판정' in generator
assert '이 판정은 어디까지 믿을 수 있을까?' in generator
assert '같은 이름의 다른 식물은 아닌가요?' in generator
assert '이 판정이 말해주지 못하는 것' in generator
assert '판정 근거 자세히 보기' in generator
assert generator.index('이 판정이 말해주지 못하는 것') < generator.index('판정 근거 자세히 보기')
assert '영양성분은 참고자료로 확인하세요' in generator
assert '원논문·학술자료' in generator
assert '다른 식물도 확인하기' in generator
assert 'exact_by_plant' in generator
assert 'assessment_scope' in generator and 'exact_species' in generator
assert '종별 특이사항' in generator
assert '특정 종에서만 확인된 근거다. 다른 육지거북 종에도 같다고 가정하지 않는다.' in generator
assert 'species-specific' in generator and 'speciesexception' in generator
assert '<div class="decisionlabel">3초 결론</div>' in generator
assert '세부 대상종은 아래 원자료에서 확인' in generator
assert 'taxon_note=' not in generator
assert '먹여도 되는지 먼저 확인하고, 필요한 경우 근거와 한계까지 내려가며 확인할 수 있다.' in generator
assert 'nutrition_section_no' not in generator
assert 'scholarly_section_no' not in generator
assert 'related_section_no' not in generator
assert '<h2>6. 야생에서는 실제로 어떻게 먹었나?</h2>' not in generator
assert '<h2>영양성분은 참고자료로 확인하세요</h2>' in generator
assert '<h2>원논문·학술자료</h2>' in generator
assert generator.count('<h2>이 판정이 말해주지 못하는 것</h2>') == 1
assert generator.index('<h2>이 판정이 말해주지 못하는 것</h2>') < generator.index('<h2>판정 근거 자세히 보기</h2>')
assert generator.index('<h2>판정 근거 자세히 보기</h2>') < generator.index('<h2>영양성분은 참고자료로 확인하세요</h2>')
assert 'interpretation_html=' not in generator
assert '<h2>실제 급여에서는 이렇게 보세요</h2>' in generator
assert '<b>근거가 말하지 않는 것</b>' in generator
assert '야생 섭식 기록도 무제한 급여를 뜻하지 않는다.' in generator
assert 'class="gradekey"' in generator
assert '<b>A</b> 혼합식 활용' in generator
assert '<b>B</b> 제한적 혼합' in generator
assert '<b>C</b> 가끔 보조' in generator
assert '<b>D</b> 급여 제외' in generator
assert 'grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin:12px 0' in generator
assert '근거가 다루는 부위</b><strong>{esc(part_note)}' not in generator
assert '확인된 부위·상태</b><p>{esc(part_note)}' in generator
assert 'class="skiplink" href="#main-content"' in generator
assert '<main id="main-content">' in generator
assert 'a:focus-visible,button:focus-visible' in generator
assert '.decision{{padding:26px 28px' in generator
assert '.practical{{margin-top:16px}}' in generator
assert '.detailnav{{margin-bottom:22px;padding-bottom:12px}}' in generator
assert '.decisionwhy{{font-size:15px;line-height:1.62}}' in generator
assert 'decisionrule' in generator
assert '<b>결론</b><strong>{esc(label)}</strong>' not in generator
assert '<b>판정 핵심</b><br>{esc(summary)}' not in generator
assert '직접 {direct_count} · 전문 사육 {husbandry_count} · 간접·맥락 {indirect_count}' in generator
assert 'class="card evidence-deep"' in generator
assert '여기부터는 결론의 근거를 직접 확인하고 싶은 사람을 위한 상세 자료다.' in generator
# Evidence-only architecture: retired recommendation/recording routes must never
# be reintroduced into the shared plant-detail enhancer.
for retired in ['today/','meal/?add=','그래서 오늘 뭐 먹이지?','이 먹이 급여기록에 추가']:
    assert retired not in js, retired
assert "glob('*/index.html')" in inj
assert '@media(max-width:620px)' in css
registry=json.loads((root/'data/verified_plant_images_v56.json').read_text(encoding='utf-8'))
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
print(f'plant detail v5.6 evidence-only enhancer audit OK for {expected} pages; {len(seen)} verified images')
