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
public = [p for p in plants if p.get('suitability_status') != 'unreviewed' and p.get('identity_status') != 'candidate_name']
assert len(public) == 69, len(public)
assert "현재 등록된 '+plants.length+'종" in html
assert "전체 식물 보기" in html
assert "전체 식물 69종 보기" not in html
assert 'href="./all-plants/"' in html
assert 'href="./core-foods/"' in html
# Retired recommendation / husbandry-recording entry points must not return.
for retired in ('./today/','./meal/','./weekly/','./growth/','./monthly/','./trends/','./profile/','./settings/'):
    assert retired not in html, retired
for retired_copy in ('오늘 식단 후보 보기','자주 찾는 핵심 먹이 9종','사육 기록','프로필 관리','7일 식단','30일 요약','장기 추세','백업·복원'):
    assert retired_copy not in html, retired_copy
# The home page generates the 12 addendum URLs at runtime.
assert "Array.from({length:12}" in html
assert "assessments_korea_addendum'+(i?'_'+(i+1):'')+'.json'" in html
# Naver/blog links can land on /?q=<food> and must auto-run the public search.
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
