from pathlib import Path
import re
R=Path(__file__).resolve().parents[1]
js=(R/'candidate-mobile-evidence-summary.js').read_text(encoding='utf-8')
ctx=(R/'profile-context.js').read_text(encoding='utf-8')
sw=(R/'sw.js').read_text(encoding='utf-8')
m=re.search(r"const CACHE='tfd-v(\d+)-stable-(\d+)'",sw)
checks={
 'file_exists':(R/'candidate-mobile-evidence-summary.js').exists(),
 'today_only':'/today' in js or '\\/today' in js,
 'loads_after_candidate_context':'candidate-applicability-summary.js' in ctx and 'candidate-mobile-evidence-summary.js' in ctx and 'c.onload' in ctx,
 'three_summary_axes':'applicability-chip' in js and 'frequency-chip' in js and 'quality-chip' in js,
 'source_quality':'학술문헌' in js and '공식·공공 DB' in js and '전문기관 자료' in js,
 'frequency_not_ratio':'빈도 미구조화' in js and 'frequency-chip' in js,
 'mobile_collapsed':"max-width:640px" in js and "details.open=!matchMedia" in js and '근거 맥락 자세히 보기' in js,
 'detail_preserved':'children.forEach(n=>body.appendChild(n))' in js,
 'no_verdict_recalc':'verdict' not in js.lower() and 'rank' not in js.lower(),
 'cache_file':"'./candidate-mobile-evidence-summary.js'" in sw,
 'cache_current':bool(m) and int(m.group(1))>=51 and int(m.group(2))>=23,
}
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
failed=[k for k,v in checks.items() if not v]
if failed: raise SystemExit('Mobile evidence summary audit failed: '+', '.join(failed))
print('Mobile evidence summary audit PASS')
