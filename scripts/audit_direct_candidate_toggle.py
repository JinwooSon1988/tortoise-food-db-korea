from pathlib import Path
import re
R=Path(__file__).resolve().parents[1]
js=(R/'source-preview.js').read_text(encoding='utf-8')
sw=(R/'sw.js').read_text(encoding='utf-8')
m=re.search(r"const CACHE='tfd-v(\d+)-stable-(\d+)'",sw)
checks={
 'toggle_control':'directCandidateOnly' in js and '이베라 1차 직접근거 있는 후보만 보기' in js,
 'default_all':"candidateMode:'all'" in js,
 'primary_only_semantics':"state.candidateMode==='primary'" in js and "candidateKind(label)==='primary'" in js,
 'ibera_profile_guard':"species==='ibera'" in js and '이 토글은 이베라(Testudo graeca ibera) 프로필에서만 사용한다.' in js,
 'hide_not_reorder':'label.hidden=!show' in js,
 'unselect_hidden':'cb.checked=false' in js and "dispatchEvent(new Event('change'" in js,
 'empty_state':'이베라 1차 직접근거가 연결된 후보가 현재 목록에 없다.' in js,
 'no_safety_inference':'직접근거 미연결은 위험·부적합을 뜻하지 않는다' in js,
 'summary_visible_count':'표시 후보 ' in js and '전체 후보 ' in js,
 'cache_current_enough':bool(m) and int(m.group(1))>=51 and int(m.group(2))>=12,
}
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
failed=[k for k,v in checks.items() if not v]
if failed: raise SystemExit('Direct candidate toggle audit failed: '+', '.join(failed))
print('Direct candidate toggle audit PASS')
