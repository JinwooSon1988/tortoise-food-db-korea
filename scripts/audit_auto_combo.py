from pathlib import Path
R=Path(__file__).resolve().parents[1]
h=(R/'today/index.html').read_text(encoding='utf-8')
sw=(R/'sw.js').read_text(encoding='utf-8')
checks={
 'combo3':'3종 조합 만들기' in h,
 'combo4':'4종 조합 만들기' in h,
 'allowed_only':'const ALLOWED=new Set' in h,
 'uses_family_diversity':'families=new Set' in h and '.family' in h,
 'recent_rotation':'recentCounts' in h and '최근 7일' in h,
 'pantry_respected':'if(only)rows=rows.filter' in h,
 'no_quantity_claim':'급여량 비율을 제시하지 않는다' in h,
 'no_completeness_claim':'영양 균형을 보장하지 않는다' in h,
 'meal_handoff':'../meal/?add=' in h,
 'cache_bumped':'tfd-v51-stable-5' in sw,
}
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
failed=[k for k,v in checks.items() if not v]
if failed: raise SystemExit('Auto combo audit failed: '+', '.join(failed))
print('Auto combo audit PASS')
