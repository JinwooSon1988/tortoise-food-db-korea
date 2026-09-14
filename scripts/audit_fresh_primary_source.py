from pathlib import Path
import re
R=Path(__file__).resolve().parents[1]
js=(R/'fresh-primary-combo-explain.js').read_text(encoding='utf-8')
sw=(R/'sw.js').read_text(encoding='utf-8')
m=re.search(r"const CACHE='tfd-v(\d+)-stable-(\d+)'",sw)
checks={
 'loads_assessments':'../data/assessments.json' in js,
 'loads_evidence':'../data/evidence.json' in js,
 'uses_linked_ids':'evidence_ids' in js and 'assessmentFor' in js,
 'strict_ibera_primary':"subspecies_direct_wild_diet" in js and 'Testudo graeca ibera' in js,
 'single_source':'return e' in js and 'linkedPrimarySource' in js,
 'source_citation':'e.citation||e.id' in js,
 'source_link':'e.url' in js and 'e.doi' in js and 'e.pmid' in js,
 'missing_not_invented':'연결된 이베라 1차 출처 메타데이터 없음' in js,
 'wild_not_ratio':('야생 관찰 빈도를 사육 급여비율로 환산하지 않으며' in js) or ('야생 관찰 빈도 분류이며 사육 급여비율이 아니다' in js),
 'no_completeness_claim':'급여량·배합률·영양완전성·건강효과' in js,
 'cache_current_enough':bool(m) and int(m.group(1))>=51 and int(m.group(2))>=16,
}
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
failed=[k for k,v in checks.items() if not v]
if failed: raise SystemExit('Fresh primary source audit failed: '+', '.join(failed))
print('Fresh primary source audit PASS')
