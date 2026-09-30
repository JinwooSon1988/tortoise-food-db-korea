"""Home search contract (Korean public site).

Checks behaviour-level invariants instead of exact CSS/copy strings:
canonical data source, shared verdict core, no species selector or retired
features, the search → grade → reason → detail path, and filter framing.
Cross-page grade equality is enforced by scripts/qa_verdict_consistency.py.
"""
import json, re
from pathlib import Path

root = Path(__file__).resolve().parents[1]
html = (root / 'index.html').read_text(encoding='utf-8')
search_live = (root / 'search-live.js').read_text(encoding='utf-8')
core = (root / 'verdict-core.js').read_text(encoding='utf-8')
plants = json.loads((root / 'data' / 'plants.json').read_text(encoding='utf-8'))
assessment_data = json.loads((root / 'data' / 'public_assessments.json').read_text(encoding='utf-8'))
assessments = assessment_data if isinstance(assessment_data, list) else assessment_data.get('assessments', assessment_data.get('records', []))
script = re.search(r'<script>([\s\S]*?)</script></body>', html).group(1)

# Data: canonical registry only; candidates stay out of public results.
assert len(plants) >= 69, len(plants)
assert any(p.get('identity_status') == 'candidate_name' for p in plants), 'catalog must retain explicit candidate records'
assert "j('./data/public_assessments.json')" in script
assert 'assessments_korea_addendum' not in html + search_live and "'./data/assessments.json'" not in html + search_live
assert "isPublic:p.identity_status!=='candidate_name'&&assessedIds.has(p.id)" in script
assert 'if(!r.isPublic)return false' in script

# Verdicts come from the shared core; the home never re-implements or overrides them.
assert html.index('./verdict-core.js') < html.index('<script>\n'), 'verdict-core.js must load before the inline search script'
assert 'TV.representative(' in script and 'TV.display(' in script and 'TV.speciesNotes(' in script
assert 'const GRADE=' not in script and 'const V=' not in script, 'grade tables must live in verdict-core.js only'
for v in ('supported_mixed_diet', 'limited_mixed_diet', 'limited_supplement', 'do_not_feed'):
    assert v in core
assert "grade:'보류'" in core, 'unresolved verdicts must render as 판정 보류, not as a letter grade'
assert 'replaceWith(verdict)' not in search_live and '.badge' not in search_live, 'no script may rewrite result verdicts'

# No species selector and no retired personal features.
for banned in ('id="animalSelect"', 'selectedAnimal', 'tortoiseAnimalTaxon', '.speciesbar{'):
    assert banned not in html + search_live, banned
for retired in ('./today/', './meal/', './weekly/', './growth/', './monthly/', './trends/', './profile/', './settings/'):
    assert retired not in html, retired
for retired_copy in ('오늘 식단 후보', '7일 식단', '30일 요약', '사육 기록', '프로필 관리', '백업·복원'):
    assert retired_copy not in html, retired_copy

# Search path: input → result card (grade, meaning, why) → detail CTA.
assert 'id="searchInput" type="search"' in html and 'aria-controls="searchResults"' in html and 'enterkeyhint="search"' in html
assert 'id="searchResults" role="status" aria-live="polite"' in html
card_fn = re.search(r'function card\(r\)\{[\s\S]*?\nfunction render', script).group(0)
card_markup = card_fn[card_fn.index("return '<article"):]
order = [card_markup.find(x) for x in ('<h3>', 'gradepill', 'class="meaning"', 'class="why"', '+noteHtml+', 'class="detailbtn"')]
assert -1 not in order and order == sorted(order), 'result card order must be name → grade → meaning → why → species note → detail'
assert "' 상세 근거 보기\" href=\"./plant/'" in card_fn
assert "aria-label=\"'+esc(r.label)+' · '+esc(g.grade)+' '+esc(g.label)+'\"" in card_fn, 'result cards must expose textual verdicts to assistive technology'
assert '종별 특이사항 있음' in card_fn and '기본 판정과 분리해 확인' in card_fn, 'species notes must stay subordinate to the default verdict'
for noisy in ('directCount', 'confidenceLabel', '근거수준', 'applicability_note'):
    assert noisy not in card_fn, f'evidence metadata belongs on the detail page, not the result card: {noisy}'

# Result volume and ranking: paged, never silently truncated; exact Korean name first.
assert 'PAGE=8' in script and 'id="moreResults"' in script and '더 보기' in script
assert 'function matchRank(r,q)' in script and 'if(ko===q)return 0' in script
assert ".normalize('NFKC')" in script
assert "[\\s·._'’\\-–—()]+" in script
assert "matchRank(a,q)-matchRank(b,q)" in script

# Filters are framed as views, not recommendations.
assert 'aria-label="판정 등급으로 보기 (추천 목록 아님)"' in html
assert '구하는 곳' in html and '등급별 보기' in html

# Grade meaning is explained once, with the dose/frequency boundary.
assert 'class="gradeguide"' in html
for g in ('<b>A</b>', '<b>B</b>', '<b>C</b>', '<b>D</b>'):
    assert g in html
assert html.count('정해진 급여량·빈도') == 1
assert '판정 보류는 안전하다는 뜻이 아닙니다' in html
# Zero-result searches must not imply safety and must offer a recovery path without exposing candidates.
assert '먹여도 된다는 뜻이 아닙니다' in script
assert '다른 이름·영문명·학명' in script and './all-plants/' in script
assert '식물 정체성이 확정되지 않은 항목은 공개 판정에 표시하지 않습니다' in script

# Deep links (?q=) wait for the catalog instead of a copy string.
assert "new URLSearchParams(location.search).get('q')" in search_live
assert "deepQuery.slice(0,80)" in search_live
assert "dataset.ready==='1'" in search_live and "countEl.dataset.ready='1'" in script
assert "document.getElementById('searchBtn')?.click()" in search_live

assert 'href="./all-plants/"' in html and 'href="./core-foods/"' in html
assert html.count('<style') == 1 and html.count('</style>') == 1
assert '@media(prefers-reduced-motion:reduce)' in html and 'button:focus-visible,a:focus-visible,input:focus-visible' in html

ids = {p['id'] for p in plants}
assessment_ids = {a['plant_id'] for a in assessments}
for pid in ('chicory', 'chard', 'lambs_lettuce'):
    assert pid in ids and pid in assessment_ids
    assert (root / 'plant' / pid / 'index.html').exists()

print('public evidence-only home search audit: PASS')

assert html.count('data-filter="hold">보류 · 근거 부족') == 1
assert "activeFilter==='hold'" in html
assert "TV.display(a).grade==='보류'" in html

# Search-first density: keep the final override compact on desktop and mobile.
assert '.hero{padding:30px 12px 18px}' in html
assert '.hero{padding:12px 4px 11px}' in html
assert '.resultcard{display:block;padding:16px 18px' in html

# Safety/accessibility UX: restrictive verdict reasons stay fully visible and compact controls remain tappable.
assert '.grade-b .why,.grade-c .why,.grade-d .why,.grade-hold .why{display:block;-webkit-line-clamp:unset;overflow:visible}' in html
assert '.examples button{min-height:44px;' in html
assert '.quickfilter{min-height:44px;padding:7px 12px}' in html
