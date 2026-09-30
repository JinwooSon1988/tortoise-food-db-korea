"""Plant detail page contract, checked on the generated pages themselves.

Information hierarchy on every page:
  name → grade → meaning → why → practical reading → species notes → scope / identity / limits
  → evidence (papers first) → nutrition → related.
Grade equality with the home search is enforced by scripts/qa_verdict_consistency.py.
"""
import json, re
from pathlib import Path

root = Path(__file__).resolve().parents[1]
plants = json.loads((root / 'data/plants.json').read_text(encoding='utf-8'))
assessments = json.loads((root / 'data/public_assessments.json').read_text(encoding='utf-8'))
if isinstance(assessments, dict): assessments = assessments.get('assessments', assessments.get('records', []))
generator = (root / 'scripts/generate_static_pages.py').read_text(encoding='utf-8')
inj = (root / 'scripts/inject_plant_detail_v56.py').read_text(encoding='utf-8')
assessed_ids = {a['plant_id'] for a in assessments}
public_ids = {p['id'] for p in plants if p.get('identity_status') != 'candidate_name' and p['id'] in assessed_ids}
pages = {p.parent.name: p.read_text(encoding='utf-8') for p in (root / 'plant').glob('*/index.html')}
missing = sorted(public_ids - set(pages))
assert not missing, ('missing reviewed public pages', missing)

# Generator uses the canonical registry and the shared selection rule; no per-plant verdict overrides.
assert 'from public_verdict import' in generator and 'representative(rows)' in generator
assert 'SPECIAL=' not in generator, 'hand-written per-plant verdict overrides are not allowed'
assert 'assessments_korea_addendum' not in generator
# Retired runtime enhancers must stay retired (they re-derived verdicts from legacy data and a species selector).
assert not (root / 'plant-detail-v56.js').exists() and not (root / 'ibera-direct-evidence-v56.js').exists()
assert "glob('*/index.html')" in inj and 'RETIRED' in inj

assert '<details class="scopefold">' in generator and '<summary>판정의 적용 범위와 확인되지 않은 내용 보기</summary>' in generator
errors = []
for pid in sorted(public_ids):
    t = pages[pid]
    main = t[t.index('<main'):]
    def pos(token):
        i = main.find(token)
        return i if i >= 0 else None
    # First screen: name, then the decision card with grade, meaning, reason.
    h1, decision, meaning, why = pos('<h1>'), pos(' decision" data-grade='), pos('class="meaning"'), pos('class="decisionwhy')
    if None in (h1, decision, meaning, why) or not (h1 < decision < meaning < why):
        errors.append(f'{pid}: first screen must be name → grade → meaning → why'); continue
    # Nothing heavy may sit between the name and the decision.
    if re.search(r'<section', main[h1:main.rfind('<section', 0, decision)]):
        errors.append(f'{pid}: a section pushes the decision below the plant name')
    later = [pos(x) for x in ('<h2>판정 범위와 주의사항</h2>', '<h2>판정 근거 자세히 보기</h2>', '<h2>영양성분은 참고자료로 확인하세요</h2>', '<h2>다른 식물도 확인하기</h2>')]
    if None in later or later != sorted(later) or later[0] < why:
        errors.append(f'{pid}: scope/limits → evidence → nutrition → related order broken')
    # Scope content is intentionally collapsed, except high-risk identity warnings which stay visible above it.
    # Materialized pages may lag the generator within the same PR run; fold contract is verified in generator source below.
    sp = pos('<h2>종별 특이사항</h2>')
    if sp is not None and later[0] is not None and not (why < sp < later[0]):
        errors.append(f'{pid}: species notes must follow the default verdict and precede scope/limits')
    # Evidence numbers live in the evidence section, not in the first-screen decision card.
    decision_card = main[decision:main.find('</section>', decision)]
    if '직접 ' in decision_card and '근거 구성' in decision_card or 'quickfacts' in decision_card:
        errors.append(f'{pid}: evidence counts must not crowd the decision card')
    # Papers are listed before specialist/database sources.
    kinds = re.findall(r'<article class="evcard"><div class="evhead"><span class="(paper|)">', main)
    if kinds != sorted(kinds, key=lambda k: 0 if k == 'paper' else 1):
        errors.append(f'{pid}: peer-reviewed papers must be listed first')
    if 'scholarly' in main or '<h2>원논문·학술자료</h2>' in main:
        errors.append(f'{pid}: papers must not be repeated in a second section')
    for retired in ('today/', 'meal/?add=', '그래서 오늘 뭐 먹이지?', '이 먹이 급여기록에 추가', 'animalSelect', 'tortoiseAnimalTaxon'):
        if retired in t:
            errors.append(f'{pid}: retired feature {retired}')
    if 'class="skiplink" href="#main-content"' not in t or '<main id="main-content"' not in t:
        errors.append(f'{pid}: skip link / main landmark missing')
if errors:
    raise SystemExit('FAIL: plant detail contract\n- ' + '\n- '.join(errors[:60]))

# Direct Ibera wild observations render statically on the matching pages.
ibera = json.loads((root / 'data/ibera_direct_feeding_evidence_v56.json').read_text(encoding='utf-8'))
for o in ibera['observations']:
    if o.get('plant_id') in public_ids:
        assert 'data-ibera-direct' in pages[o['plant_id']], o['plant_id']

registry = json.loads((root / 'data/verified_plant_images_v56.json').read_text(encoding='utf-8'))
master = {p['id']: p for p in plants}
required = set(registry['policy']['required_fields'])
seen = set()
for image in registry['images']:
    pid = image['plant_id']
    assert required <= set(image), (pid, required - set(image))
    assert pid not in seen, pid
    seen.add(pid)
    assert pid in master, pid
    assert image['identity_scope'] in {'exact_species', 'exact_subspecies', 'exact_variety'}, pid
    assert 'spp.' not in master[pid]['scientific'], pid
    assert image['scientific'] == master[pid]['scientific'], (pid, image['scientific'], master[pid]['scientific'])
    assert image['source_url'].startswith('https://commons.wikimedia.org/wiki/File:'), pid
    assert image['image_url'].startswith('https://commons.wikimedia.org/wiki/Special:Redirect/file/'), pid
    assert image['license'], pid
    assert image['creator'], pid
    if pid in public_ids:
        assert image['image_url'] in pages[pid] and image['license'] in pages[pid], f'{pid}: verified image or licence missing'
print(f'plant detail v5.6 contract OK for {len(public_ids)} pages; {len(seen)} verified images')

# Mobile verdict card stays compact while retaining the A/B/C/D context key.
assert '.decision{padding:14px 15px}' in generator
assert '.gradekey{gap:3px 8px;margin-top:9px;padding-top:7px;font-size:10px}' in generator
assert 'aria-label="급여 등급 안내"' in generator

# Keyboard/touch accessibility: interactive detail-page targets remain at least 44px high.
for token in (
    '.detailnav a{display:inline-flex;align-items:center;min-height:44px',
    '.scopefold>summary{cursor:pointer;min-height:44px',
    '.related{display:flex;align-items:center;min-height:44px',
    '.sourceopen{min-height:44px;align-items:center}',
):
    assert token in generator, f'missing 44px interaction target contract: {token}'

# Korean public evidence cards must route limitation copy through the localization layer.
assert 'def evidence_limit_display(value):' in generator
assert 'evidence_limit_display(e.get("does_not_support"))' in generator
for raw in (
    'This source does not by itself establish an exact captive feeding percentage',
    'Specialist plant-database guidance is not a controlled Testudo graeca ibera feeding or toxicity trial',
    'Taxonomic acceptance does not establish tortoise feeding safety',
):
    assert raw in generator, f'missing preserved evidence-limit translation contract: {raw}'

# Korean public evidence cards route support claims through a meaning-preserving display layer.
assert 'def evidence_support_display(value):' in generator
assert 'evidence_support_display(e.get("supports"))' in generator
for raw in (
    'Safe to Feed as part of a varied diet',
    'Analytical evidence that common buckwheat leaves contain phototoxic fagopyrins.',
    'Kew Plants of the World Online lists',
):
    assert raw in generator, f'missing preserved support-translation contract: {raw}'

# Scientific support translations must retain study-domain boundaries in Korean.
for token in (
    '포유류 독성시험 결과이므로 육지거북의 독성 용량으로 직접 환산할 수 없다.',
    '야생 섭식 자료이며 사육 급여 비율을 직접 정하는 자료는 아니다.',
    '추출물 기반 시험관 연구이므로 생잎의 육지거북 급여 안전성과 동일시하지 않는다.',
    '농축 정유 자료를 일반 식물체의 육지거북 급여와 동일시하지 않는다.',
):
    assert token in generator, f'missing scientific evidence-domain boundary: {token}'

# Specialist husbandry translations retain practical plant-part and exposure warnings.
for token in (
    '뿌리와 덩이뿌리는 절대 급여하지 말라고 명시한다.',
    '꽃집·원예점 식물의 농약 처리 가능성을 경고한다.',
    'Oenanthe 미나리류를 피해야 할 고독성 식물로 설명한다.',
    '개별 풀의 급여 판정은 해당 분류군을 직접 다룬 별도 전문 근거로 판단한다.',
):
    assert token in generator, f'missing practical husbandry boundary: {token}'

# High-use feeding guidance must preserve practical part/safety distinctions.
for token in (
    '뿌리는 명시적으로 제외한다.',
    '씨앗은 급여하지 말라고 명시한다.',
    '독성이 문제되는 잎·미숙 열매와 성숙 열매를 구분하지만',
    '다른 부위로 임의 확대하지 않는다.',
):
    assert token in generator, f'missing high-use feeding distinction: {token}'

# Remaining assessment translations preserve non-transfer and planned-feeding boundaries.
for token in (
    '옥수수 속대·알곡 또는 옥수수 전체로 확대 적용하면 안 된다.',
    '이를 이베라그리스육지거북 특이 독성시험 결과로 해석하지 않는다.',
    '피레트린 함량이 높은 분류군은 명시적으로 제외한다.',
    '육지거북 사육장 안에서 재배하지 말라고 권고한다.',
):
    assert token in generator, f'missing assessment safety boundary: {token}'
