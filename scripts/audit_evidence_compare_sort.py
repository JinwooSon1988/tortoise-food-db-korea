from pathlib import Path
import re
R=Path(__file__).resolve().parents[1]
js=(R/'candidate-evidence-compare.js').read_text(encoding='utf-8')
ctx=(R/'profile-context.js').read_text(encoding='utf-8')
sw=(R/'sw.js').read_text(encoding='utf-8')
m=re.search(r"const CACHE='tfd-v(\d+)-stable-(\d+)'",sw)
checks={
 'file_exists':(R/'candidate-evidence-compare.js').exists(),
 'today_only':'/today' in js or '\\/today' in js,
 'loaded_after_mobile':'candidate-mobile-evidence-summary.js' in ctx and 'candidate-evidence-compare.js' in ctx and 'm.onload' in ctx,
 'three_evidence_axes':'applicability-chip' in js and 'frequency-chip' in js and 'quality-chip' in js,
 'compare_modes':'정확한 종 근거 우선' in js and '빈도 자료 있음 우선' in js and '학술출처 우선' in js,
 'exact_group_only':"r.applicability==='정확한 종 직접근거'?0:1" in js,
 'frequency_presence_only':'빈도 미구조화' in js and '빈도 미등록' in js and 'High' not in js and 'Moderate' not in js and 'Low' not in js,
 'stable_existing_order':'key(a)-key(b)||a.index-b.index' in js,
 'does_not_reorder_candidates':'.appendChild(label)' not in js and '.insertBefore(label' not in js and 'sort((a,b)=>key(a)-key(b)||a.index-b.index)' in js,
 'not_recommendation':'먹이 추천 점수나 급여 우선순위가 아니며' in js,
 'preserves_algorithms':'실제 후보 목록·판정·필터·빠른 조합 순서는 바꾸지 않는다' in js,
 'visible_only':'filter(x=>!x.hidden)' in js,
 'cache_file':"'./candidate-evidence-compare.js'" in sw,
 'cache_current':bool(m) and int(m.group(1))>=51 and int(m.group(2))>=24,
}
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
failed=[k for k,v in checks.items() if not v]
if failed: raise SystemExit('Evidence compare sort audit failed: '+', '.join(failed))
print('Evidence compare sort audit PASS')
