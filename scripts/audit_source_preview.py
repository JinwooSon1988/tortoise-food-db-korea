from pathlib import Path
import re
R=Path(__file__).resolve().parents[1]
js=(R/'source-preview.js').read_text(encoding='utf-8')
ctx=(R/'profile-context.js').read_text(encoding='utf-8')
sw=(R/'sw.js').read_text(encoding='utf-8')
m=re.search(r"const CACHE='tfd-v(\d+)-stable-(\d+)'",sw)
checks={
 'source_file_exists':(R/'source-preview.js').exists(),
 'today_only_loader':"/\\/today\\/?(?:index\\.html)?$/" in ctx and "source-preview.js" in ctx,
 'loads_evidence':'../data/evidence.json' in js,
 'loads_assessments':'../data/assessments.json' in js,
 'uses_evidence_ids':'evidence_ids' in js,
 'max_two':'slice(0,2)' in js and '최대 2개' in js,
 'citation_shown':'.citation' in js,
 'doi_url_support':'https://doi.org/' in js,
 'pmid_url_support':'pubmed.ncbi.nlm.nih.gov' in js,
 'does_not_infer_missing':('연결된 공개 출처 메타데이터 없음' in js or '현재 필터에 맞는 연결 출처 없음' in js),
 'no_recalculation_claim':('전체 판정을 재계산하지 않는다' in js or '식물 판정·후보 순위·급여량·영양완전성은 다시 계산하지 않는다' in js),
 'dynamic_dom_support':'MutationObserver' in js,
 'cache_source_preview':"'./source-preview.js'" in sw,
 'cache_evidence':"'./data/evidence.json'" in sw,
 'cache_current_enough':bool(m) and int(m.group(1))>=51 and int(m.group(2))>=8,
}
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
failed=[k for k,v in checks.items() if not v]
if failed: raise SystemExit('Source preview audit failed: '+', '.join(failed))
print('Source preview audit PASS')
