from pathlib import Path
import json,re
R=Path(__file__).resolve().parents[1]
js=(R/'candidate-evidence-lineage.js').read_text(encoding='utf-8')
ctx=(R/'profile-context.js').read_text(encoding='utf-8')
sw=(R/'sw.js').read_text(encoding='utf-8')
data=json.loads((R/'data/evidence_lineage.json').read_text(encoding='utf-8'))
by={x['plant_id']:x for x in data}
m=re.search(r"const CACHE='tfd-v(\d+)-stable-(\d+)'",sw)
checks={
 'six_structured_records':len(data)==6 and set(by)=={'dandelion','sowthistle','clover','alfalfa','chicory','dolnamul'},
 'dandelion_exact':by.get('dandelion',{}).get('plant_match_level')=='exact_species' and by['dandelion']['reported_taxa']==['Taraxacum officinale'],
 'sowthistle_genus':by.get('sowthistle',{}).get('plant_match_level')=='genus_only' and by['sowthistle']['reported_taxa']==['Sonchus sp.'],
 'clover_genus':by.get('clover',{}).get('plant_match_level')=='genus_only' and by['clover']['reported_taxa']==['Trifolium sp.'],
 'alfalfa_genus':by.get('alfalfa',{}).get('plant_match_level')=='genus_only' and by['alfalfa']['reported_taxa']==['Medicago sp.'],
 'chicory_exact':by.get('chicory',{}).get('plant_match_level')=='exact_species' and by['chicory']['reported_taxa']==['Cichorium intybus'],
 'dolnamul_congeneric':by.get('dolnamul',{}).get('plant_match_level')=='congeneric_species' and set(by['dolnamul']['reported_taxa'])=={'Sedum rubens','Sedum album'},
 'non_ratio_limits':all(('급여비율' in x.get('application_limit','') or '급여량' in x.get('application_limit','') or '종 수준' in x.get('application_limit','')) for x in data),
 'four_stage_ui':all(x in js for x in ['1 · DB 식물','2 · 논문 기록 식물','3 · 이베라 관찰','4 · 사육 적용 한계']),
 'axes_independent':'이베라 직접근거와 식물 종 일치도는 서로 다른 축이다' in js,
 'missing_no_inference':'현재 구조화된 이베라 직접 근거 계보 없음' in js and '임의로 추론해 만들지 않는다' in js,
 'source_linked':'연결 1차 출처' in js and 'source_id' in js and 'citation' in js,
 'no_feed_calc':'급여량·배합률·영양완전성·건강효과를 계산하지 않는다' in js,
 'loaded_after_compare':'candidate-evidence-compare.js' in ctx and 'candidate-evidence-lineage.js' in ctx and 'v.onload' in ctx,
 'cache_assets':"'./candidate-evidence-lineage.js'" in sw and "'./data/evidence_lineage.json'" in sw,
 'cache_current':bool(m) and int(m.group(1))>=51 and int(m.group(2))>=25,
}
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
failed=[k for k,v in checks.items() if not v]
if failed: raise SystemExit('Evidence lineage audit failed: '+', '.join(failed))
print('Evidence lineage audit PASS')
