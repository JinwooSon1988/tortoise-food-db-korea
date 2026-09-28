import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
html = (root / 'index.html').read_text(encoding='utf-8')
search_live = (root / 'search-live.js').read_text(encoding='utf-8')
plants = json.loads((root / 'data' / 'plants.json').read_text(encoding='utf-8'))
base = json.loads((root / 'data' / 'assessments.json').read_text(encoding='utf-8'))
addenda = []
for i in range(1, 13):
    name = 'assessments_korea_addendum.json' if i == 1 else f'assessments_korea_addendum_{i}.json'
    addenda += json.loads((root / 'data' / name).read_text(encoding='utf-8'))
assessments = base + addenda

assert len(plants) >= 69, len(plants)
candidate = [p for p in plants if p.get('identity_status') == 'candidate_name']
assert len(candidate) >= 1, 'catalog expansion must retain explicit candidate records'
assert "const publicCount=plantCatalog.filter(r=>r.isPublic).length" in html
assert html.index("plantCatalog=plants.map") < html.index("const publicCount=plantCatalog.filter")
assert '<style id="home-design-system-20260928">' in html
assert html.count('<style') == 1 and html.count('</style>') == 1
assert "search-first polish" in html
assert ".truststrip{grid-template-columns:repeat(3,minmax(0,1fr))" in html
assert ".hero{padding:28px 4px 18px}" in html
assert "현재 공개 판정 '+publicCount+'종" in html
assert "if(!r.isPublic)return false" in html
assert 'aria-controls="searchResults"' in html
assert 'id="searchResults" role="status" aria-live="polite"' in html
assert 'enterkeyhint="search"' in html
assert 'aria-describedby="searchHelp"' in html
assert 'id="searchHelp" class="searchhelp"' in html
assert "direct=directCount(a)" in html
assert "function matchRank(r,q)" in html
assert 'id="animalSelect"' not in html
assert "selectedAnimal" not in html
assert ".speciesbar{" not in html
assert ".specieshint{" not in html
assert "function scopeLabel(a)" in html
assert "function speciesNotes(id,primary)" in html
assert "x.assessment_scope==='exact_species'&&x.animal_taxon&&x.animal_taxon!=='Testudo'" in html
assert "종별 특이사항" in html
assert "육지거북 일반 근거" in html
assert "지중해 Testudo 근거" in html
assert "terms.some(x=>x===q)" in html
assert "terms.some(x=>x.startsWith(q))" in html
assert "matchRank(a,q)-matchRank(b,q)||directCount(best(b.plant_id))-directCount(best(a.plant_id))" in html
assert 'class="evidencequick"' in html
assert "직접근거 '+direct+'건" in html
assert ".grade-a{border-left:4px" in html and ".grade-d{border-left:4px" in html
assert "전체 식물 보기" in html
assert "전체 식물 69종 보기" not in html
assert 'href="./all-plants/"' in html
assert 'href="./core-foods/"' in html
for retired in ('./today/','./meal/','./weekly/','./growth/','./monthly/','./trends/','./profile/','./settings/'):
    assert retired not in html, retired
for retired_copy in ('오늘 식단 후보 보기','자주 찾는 핵심 먹이 9종','사육 기록','프로필 관리','7일 식단','30일 요약','장기 추세','백업·복원'):
    assert retired_copy not in html, retired_copy
assert "Array.from({length:12}" in html
assert "assessments_korea_addendum'+(i?'_'+(i+1):'')+'.json'" in html
assert "new URLSearchParams(location.search).get('q')" in search_live
assert "deepQuery.slice(0,80)" in search_live
assert "document.getElementById('searchBtn')?.click()" in search_live

ids = {p['id'] for p in plants}
assessment_ids = {a['plant_id'] for a in assessments}
for pid in ('chicory','chard','lambs_lettuce'):
    assert pid in ids
    assert pid in assessment_ids
    assert (root / 'plant' / pid / 'index.html').exists()

print('public evidence-only home search audit: PASS')
