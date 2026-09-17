from pathlib import Path
import re
R=Path(__file__).resolve().parents[1]
js=(R/'source-preview.js').read_text(encoding='utf-8')
sw=(R/'sw.js').read_text(encoding='utf-8')
# Cache naming changed when unstable recommendation/recording surfaces were retired.
m=re.search(r"const CACHE='tfd-v(\d+)-(?:stable|evidence-only)-(\d+)'",sw)
checks={
 'global_filter_card':'근거 출처 필터' in js and 'source-filter-card' in js,
 'all_mode':'data-source-mode="all"' in js,
 'ibera_mode':'이베라 1차 직접근거만' in js and "state.mode==='ibera'" in js,
 'quality_mode':'학술·공식근거만' in js and "state.mode==='quality'" in js,
 'ibera_primary_only':'isIberaPrimary(e)' in js and "if(state.mode==='ibera')return isIberaPrimary(e)" in js,
 'quality_uses_q1':"qualityBadge(e)[2]==='q1'" in js,
 'official_types':'official_database' in js and 'official_agriculture_database' in js and 'official_biodiversity_agriculture' in js,
 'display_only_warning':'출처 표시 범위만 바꾼다' in js,
 'no_verdict_recalc':'다시 계산하지 않는다' in js,
 'empty_state':'현재 필터에 맞는 연결 출처 없음' in js,
 'dynamic_refresh':'MutationObserver' in js,
 'cache_current_enough':bool(m) and int(m.group(1))>=5 and int(m.group(2))>=10,
}
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
failed=[k for k,v in checks.items() if not v]
if failed: raise SystemExit('Evidence filter audit failed: '+', '.join(failed))
print('Evidence filter audit PASS')
