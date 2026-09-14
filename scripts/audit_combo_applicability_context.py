from pathlib import Path
import re
R=Path(__file__).resolve().parents[1]
js=(R/'combo-applicability-context.js').read_text(encoding='utf-8')
ctx=(R/'profile-context.js').read_text(encoding='utf-8')
sw=(R/'sw.js').read_text(encoding='utf-8')
m=re.search(r"const CACHE='tfd-v(\d+)-stable-(\d+)'",sw)
checks={
 'file_exists':(R/'combo-applicability-context.js').exists(),
 'today_only':'/today' in js or '\\/today' in js,
 'loads_after_applicability':'candidate-applicability-summary.js' in ctx and 'combo-applicability-context.js' in ctx and 'c.onload' in ctx,
 'reads_mode':'TFDCandidateApplicability' in js and ('mode?.()' in js or '.mode()' in js),
 'three_mode_labels':'정확한 종 직접근거만' in js and '속 수준 포함' in js and '전체 적용성' in js,
 'excluded_summary':'이 기준으로 제외' in js and 'excludedByApplicability' in js,
 'no_safety_inference':'안전성·부적합 판정이 아니라' in js,
 'no_prescriptive_claims':'균형식' not in js and '최적' not in js and '권장량' not in js,
 'invalidates_old_explain':'기존 조합 설명은 이전 기준과 섞이지 않도록 지웠다' in js and "tfd:applicability-filter-changed" in js,
 'fresh_combo_hook':'freshCombo3' in js and 'addContext' in js,
 'cache_file':"'./combo-applicability-context.js'" in sw,
 'cache_current':bool(m) and int(m.group(1))>=51 and int(m.group(2))>=21,
}
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
failed=[k for k,v in checks.items() if not v]
if failed: raise SystemExit('Combo applicability context audit failed: '+', '.join(failed))
print('Combo applicability context audit PASS')
