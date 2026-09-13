from pathlib import Path
R=Path(__file__).resolve().parents[1]
h=(R/'today/index.html').read_text(encoding='utf-8')
checks={
 'pantry_storage':'tfd_pantry_v1' in h,
 'profile_scoped_pantry':'profile_id' in h and 'pantryFor' in h,
 'pantry_filter_toggle':'보유 식재료만 보기' in h,
 'pantry_add_control':'보유 식재료 추가' in h,
 'pantry_remove_control':'data-pantry-remove' in h,
 'ranking_still_evidence_first':'RANK[a.verdict]' in h,
 'no_fake_score_text':'추천 점수' in h and '영양적 완전성' in h,
 'meal_handoff':'../meal/?add=' in h,
}
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
failed=[k for k,v in checks.items() if not v]
if failed: raise SystemExit('Today pantry audit failed: '+', '.join(failed))
print('Today pantry audit PASS')
