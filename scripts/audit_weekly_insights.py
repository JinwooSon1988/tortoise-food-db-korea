from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
text=(ROOT/'weekly/index.html').read_text(encoding='utf-8')
checks={
 'loads plants.json':"../data/plants.json" in text,
 'loads assessments.json':"../data/assessments.json" in text,
 'keeps local storage key':"tfd_weekly_v1" in text,
 'uses active profile linkage':"profile_id:p?p.id:null" in text,
 'deduplicates date profile food':"x.date===date&&x.food===food" in text,
 'shows recorded-day coverage':"기록일" in text,
 'shows evidence distribution':"공개 검증상태 분포" in text,
 'avoids nutrition completeness score':"영양적 완전성 점수" in text,
 'shows deleted profile without reassignment':"삭제된 개체" in text and "자동 재배정하지 않는다" in text,
 'does not hardcode old PUBLIC table':"const PUBLIC=" not in text,
}
failed=[k for k,v in checks.items() if not v]
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
if failed: raise SystemExit('weekly insight audit failed: '+', '.join(failed))
print('weekly insight audit: PASS')
