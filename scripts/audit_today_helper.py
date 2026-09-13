from pathlib import Path
import re
R=Path(__file__).resolve().parents[1]
today=(R/'today/index.html').read_text(encoding='utf-8')
meal=(R/'meal/index.html').read_text(encoding='utf-8')
home=(R/'index.html').read_text(encoding='utf-8')
sw=(R/'sw.js').read_text(encoding='utf-8')
m=re.search(r"const CACHE='tfd-v(\d+)-stable-(\d+)'",sw)
checks={
 'today_exists':(R/'today/index.html').exists(),
 'uses_profile':'TFDProfiles' in today,
 'uses_recent_weekly':'tfd_weekly_v1' in today and 'getDate()-6' in today,
 'uses_assessments':'../data/assessments.json' in today,
 'mediterranean_scope':'ibera:\'Mediterranean_Testudo\'' in today and 'greek:\'Mediterranean_Testudo\'' in today,
 'horsfield_not_auto_med':"horsfieldii:'Mediterranean_Testudo'" not in today,
 'leopard_not_auto_med':"leopard:'Mediterranean_Testudo'" not in today,
 'sulcata_scope':"sulcata:'Sulcata'" in today,
 'no_fake_score_copy':'추천 점수' in today and '영양적 완전성' in today,
 'rotation_explained':'최근 7일에 덜 반복된 항목' in today,
 'meal_prefill':'URLSearchParams(location.search)' in meal and "get('add')" in meal,
 'prefill_validates_ids':'valid.has(x)' in meal,
 'home_link':'./today/' in home,
 'pwa_today':"'./today/'" in sw,
 'cache_current_enough':bool(m) and int(m.group(1))>=51 and int(m.group(2))>=3,
}
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
failed=[k for k,v in checks.items() if not v]
if failed: raise SystemExit('Today helper audit failed: '+', '.join(failed))
print('Today helper audit PASS')
