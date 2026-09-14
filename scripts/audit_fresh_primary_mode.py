from pathlib import Path
import re
R=Path(__file__).resolve().parents[1]
js=(R/'fresh-primary-mode.js').read_text(encoding='utf-8')
ctx=(R/'profile-context.js').read_text(encoding='utf-8')
sw=(R/'sw.js').read_text(encoding='utf-8')
m=re.search(r"const CACHE='tfd-v(\d+)-stable-(\d+)'",sw)
checks={
 'quick_mode_file':(R/'fresh-primary-mode.js').exists(),
 'today_only_loader':'fresh-primary-mode.js' in ctx and 's.onload' in ctx,
 'control':'freshPrimaryOnly' in js and '빠른 선택: 이베라 1차 직접근거 + 최근 7일 미급여' in js,
 'default_off':'enabled:false' in js,
 'ibera_guard':"species==='ibera'" in js and '이 빠른 선택 모드는 이베라(Testudo graeca ibera) 프로필에서만 사용한다.' in js,
 'primary_requirement':"isPrimary(label)&&recentCount(label)===0" in js,
 'recent_count_from_rendered_log':'최근 7일' in js and 'recentCount' in js,
 'mutual_exclusion':'directCandidateOnly' in js and 'direct.checked=false' in js,
 'unselect_hidden':'cb.checked=false' in js and "dispatchEvent(new Event('change'" in js,
 'empty_state':'이베라 1차 직접근거 + 최근 7일 미급여 조건에 맞는 후보가 없다.' in js,
 'no_safety_inference':'위험하거나 부적합하다는 뜻이 아니다' in js,
 'no_nutrition_claim':'급여량·영양완전성·건강효과를 판단하지 않는다' in js,
 'summary_visible_total':'표시 후보 ' in js and '전체 후보 ' in js and '빠른 선택 모드' in js,
 'cache_file':"'./fresh-primary-mode.js'" in sw,
 'cache_current_enough':bool(m) and int(m.group(1))>=51 and int(m.group(2))>=13,
}
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
failed=[k for k,v in checks.items() if not v]
if failed: raise SystemExit('Fresh primary quick mode audit failed: '+', '.join(failed))
print('Fresh primary quick mode audit PASS')
