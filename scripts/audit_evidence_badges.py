from pathlib import Path
import re
R=Path(__file__).resolve().parents[1]
js=(R/'source-preview.js').read_text(encoding='utf-8')
sw=(R/'sw.js').read_text(encoding='utf-8')
m=re.search(r"const CACHE='tfd-v(\d+)-stable-(\d+)'",sw)
checks={
 'applicability_badge':'function applicabilityBadge' in js,
 'quality_badge':'function qualityBadge' in js,
 'ibera_direct':'이베라 직접 야생근거' in js,
 'ibera_synthesis':'이베라 종계정 종합' in js,
 'other_testudo':'다른 Testudo 직접·맥락' in js,
 'plant_identity':'식물동정 근거' in js,
 'nutrition':'영양성분 자료' in js,
 'academic_quality':'학술문헌' in js,
 'official_quality':'공식·공공 DB' in js,
 'specialist_quality':'전문기관 자료' in js,
 'axes_separated':'badgeHTML(applicabilityBadge(e))+badgeHTML(qualityBadge(e))' in js,
 'no_recalculation':('전체 판정을 재계산하지 않는다' in js or '식물 판정·후보 순위·급여량·영양완전성은 다시 계산하지 않는다' in js),
 'cache_current_enough':bool(m) and int(m.group(1))>=51 and int(m.group(2))>=9,
}
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
failed=[k for k,v in checks.items() if not v]
if failed: raise SystemExit('Evidence badge audit failed: '+', '.join(failed))
print('Evidence badge audit PASS')
