from pathlib import Path
import re
R=Path(__file__).resolve().parents[1]
js=(R/'fresh-primary-combo-explain.js').read_text(encoding='utf-8')
ctx=(R/'profile-context.js').read_text(encoding='utf-8')
sw=(R/'sw.js').read_text(encoding='utf-8')
m=re.search(r"const CACHE='tfd-v(\d+)-stable-(\d+)'",sw)
checks={
 'script_exists':(R/'fresh-primary-combo-explain.js').exists(),
 'today_only':"/\\/today\\/?(?:index\\.html)?$/" in js,
 'loads_after_quick_mode':'fresh-primary-mode.js' in ctx and 'fresh-primary-combo-explain.js' in ctx,
 'button_binding':'freshCombo3' in js and 'setTimeout(renderExplain,0)' in js,
 'explains_primary':'이베라 1차 야생섭식 직접근거 연결' in js,
 'explains_recent':'최근 7일 급여기록 0회' in js,
 'explains_family':'식물 과' in js and '과 다양성' in js,
 'shows_heading':'왜 이 3종을 골랐나' in js,
 'no_balance_claim':'급여량·배합률·영양완전성·건강효과를 계산하거나 보장하지 않는다' in js,
 'does_not_invent_family':'식물 과 정보가 없어 과 다양성 판단에는 사용하지 않음' in js,
 'cache_script':"'./fresh-primary-combo-explain.js'" in sw,
 'cache_current_enough':bool(m) and int(m.group(1))>=51 and int(m.group(2))>=15,
}
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
failed=[k for k,v in checks.items() if not v]
if failed: raise SystemExit('Fresh primary combo explain audit failed: '+', '.join(failed))
print('Fresh primary combo explain audit PASS')
