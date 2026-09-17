from pathlib import Path
import re
R=Path(__file__).resolve().parents[1]
js=(R/'source-preview.js').read_text(encoding='utf-8')
sw=(R/'sw.js').read_text(encoding='utf-8')
# Cache naming changed when the public site was reduced to the evidence-only shell.
m=re.search(r"const CACHE='tfd-v(\d+)-evidence-only-(\d+)'",sw)
checks={
 'primary_classifier':'function isIberaPrimary' in js and "subspecies_direct_wild_diet" in js,
 'synthesis_separate':'function isIberaSynthesis' in js and "subspecies_direct_diet_synthesis" in js,
 'candidate_badges':'이베라 1차 직접근거 있음' in js and '이베라 1차 직접근거 미연결' in js,
 'synthesis_badge':'이베라 종계정 종합근거 있음' in js,
 'summary_card':'direct-evidence-summary' in js and '후보 근거 한눈에 보기' in js,
 'summary_counts':'stats.primary' in js and 'stats.synthesis' in js and 'stats.none' in js,
 'candidate_scope':"#candidates label.candidate" in js,
 'no_safety_inference':'위험하거나 부적합하다는 뜻이 아니라' in js,
 'primary_filter_semantics':"if(state.mode==='ibera')return isIberaPrimary(e)" in js,
 'cache_current_enough':bool(m) and int(m.group(1))>=56 and int(m.group(2))>=101,
}
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
failed=[k for k,v in checks.items() if not v]
if failed: raise SystemExit('Direct evidence summary audit failed: '+', '.join(failed))
print('Direct evidence summary audit PASS')
