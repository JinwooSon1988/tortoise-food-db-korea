from pathlib import Path
import re
R=Path(__file__).resolve().parents[1]
h=(R/'today/index.html').read_text(encoding='utf-8')
sw=(R/'sw.js').read_text(encoding='utf-8')
m=re.search(r"const CACHE='tfd-v(\d+)-stable-(\d+)'",sw)
checks={
 'combo3':'3종 조합 만들기' in h,
 'combo4':'4종 조합 만들기' in h,
 'allowed_only':'const ALLOWED=new Set' in h,
 'uses_family_diversity':'families=new Set' in h and '.family' in h,
 'recent_rotation':('recentCounts' in h or 'function recent(' in h) and '최근 7일' in h,
 'pantry_respected':('if(only)rows=rows.filter' in h or 'if(only)r=r.filter' in h),
 'no_quantity_claim':'급여량 비율' in h,
 'no_completeness_claim':('영양 균형' in h or '영양균형' in h or '영양완전성' in h),
 'meal_handoff':'../meal/?add=' in h,
 'cache_current_enough':bool(m) and int(m.group(1))>=51 and int(m.group(2))>=5,
}
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
failed=[k for k,v in checks.items() if not v]
if failed: raise SystemExit('Auto combo audit failed: '+', '.join(failed))
print('Auto combo audit PASS')
