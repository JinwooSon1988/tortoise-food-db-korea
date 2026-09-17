from pathlib import Path

home=Path('index.html').read_text(encoding='utf-8')
catalog=Path('all-plants/index.html').read_text(encoding='utf-8')
sw=Path('sw.js').read_text(encoding='utf-8')

for banned in ['./today/','./meal/','./weekly/','./growth/','./monthly/','./trends/','./profile/','./settings/','오늘 뭐 먹일까','오늘 식단 후보']:
    assert banned not in home, f'legacy public feature still exposed on home: {banned}'
assert './all-plants/' in home
assert '전체 식물 69종 보기' in home
for token in ['data-k="verdictRank"','data-k="category"','data-k="family"','data-k="calcium"','data-k="fiber"','sortDir','plant_nutrition_v56.json','rda_food_composition_v56.json']:
    assert token in catalog, f'missing catalog capability: {token}'
for banned in ["'./today/'","'./meal/'","'./weekly/'","'./growth/'","'./monthly/'","'./trends/'","'./profile/'","'./settings/'"]:
    assert banned not in sw, f'legacy feature still pre-cached: {banned}'
assert 'Promise.allSettled' in sw, 'service worker install must not fail as one optional asset fails'
print('evidence-only public UI v5.6: OK')
