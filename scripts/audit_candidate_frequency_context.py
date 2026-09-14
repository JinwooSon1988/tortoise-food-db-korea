from pathlib import Path
import re
R=Path(__file__).resolve().parents[1]
js=(R/'candidate-applicability-summary.js').read_text(encoding='utf-8')
sw=(R/'sw.js').read_text(encoding='utf-8')
freq=(R/'data'/'wild_observation_frequency.json').read_text(encoding='utf-8')
m=re.search(r"const CACHE='tfd-v(\d+)-stable-(\d+)'",sw)
checks={
 'frequency_data_used':'wild_observation_frequency.json' in js and 'frequencyContextFor' in js,
 'candidate_badge':'야생 관찰 빈도 · 급여비율 아님' in js and 'candidate-frequency-label' in js,
 'reported_taxon':'논문 기록 분류군:' in js and 'taxon_reported' in js,
 'no_fabrication':'현재 구조화된 식물별 빈도값 없음' in js and '숫자를 만들지 않는다' in js,
 'feeding_ratio_warning':'사육 급여비율' in js and '급여비율 아님' in js,
 'applicability_kept':'정확한 종 직접근거' in js and '속 수준 직접근거' in js,
 'no_nutrition_claim':'급여량·배합률·영양완전성·건강효과를 판단하지 않는다' in js,
 'known_frequency_classes':'Moderate' in freq and 'High' in freq and 'Low' in freq,
 'cache_current':bool(m) and int(m.group(1))>=51 and int(m.group(2))>=22,
}
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
failed=[k for k,v in checks.items() if not v]
if failed: raise SystemExit('Candidate frequency context audit failed: '+', '.join(failed))
print('Candidate frequency context audit PASS')
