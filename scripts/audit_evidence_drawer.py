from pathlib import Path
R=Path(__file__).resolve().parents[1]
h=(R/'today/index.html').read_text(encoding='utf-8')
sw=(R/'sw.js').read_text(encoding='utf-8')
checks={
 'drawer_present':'판정 근거 펼쳐보기' in h and 'details.evidence' in h,
 'uses_assessment_why':"a.why||'공개 설명 없음'" in h,
 'uses_applicability':'a.applicability_note' in h,
 'limits_capped':'a.limits.slice(0,3)' in h,
 'no_invented_gap_fill':'공개 설명 없음' in h,
 'no_quantity_claim':'급여량·배합률·영양완전성·건강효과를 새로 계산하지 않는다' in h,
 'combo_drawer':'evidenceDrawer(r.a)' in h,
 'candidate_drawer':'evidenceDrawer(r.a)' in h,
 'full_detail_link':'전체 상세·출처 보기' in h,
 'cache_bumped':'tfd-v51-stable-7' in sw,
}
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
failed=[k for k,v in checks.items() if not v]
if failed: raise SystemExit('Evidence drawer audit failed: '+', '.join(failed))
print('Evidence drawer audit PASS')
