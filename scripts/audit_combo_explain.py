from pathlib import Path
import re
R=Path(__file__).resolve().parents[1]
h=(R/'today/index.html').read_text(encoding='utf-8')
sw=(R/'sw.js').read_text(encoding='utf-8')
m=re.search(r"const CACHE='tfd-v(\d+)-stable-(\d+)'",sw)
checks={
 'why_heading':'왜 이 조합인가' in h,
 'explains_evidence':'LABEL[r.a.verdict]' in h,
 'explains_recent_use':'최근 7일' in h and 'r.count' in h,
 'explains_family':'다른 식물 과 확보' in h,
 'no_balance_claim':'영양완전성' in h or '영양균형' in h,
 'no_quantity_claim':'급여량 비율' in h,
 'keeps_allowed_filter':'const ALLOWED=new Set' in h,
 'keeps_pantry':'tfd_pantry_v1' in h,
 'keeps_meal_handoff':'../meal/?add=' in h,
 'cache_current_enough':bool(m) and int(m.group(1))>=51 and int(m.group(2))>=6,
}
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
failed=[k for k,v in checks.items() if not v]
if failed: raise SystemExit('Combo explanation audit failed: '+', '.join(failed))
print('Combo explanation audit PASS')
