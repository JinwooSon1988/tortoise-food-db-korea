from pathlib import Path
import re
R=Path(__file__).resolve().parents[1]
js=(R/'candidate-applicability-summary.js').read_text(encoding='utf-8')
fresh=(R/'fresh-primary-mode.js').read_text(encoding='utf-8')
sw=(R/'sw.js').read_text(encoding='utf-8')
m=re.search(r"const CACHE='tfd-v(\d+)-stable-(\d+)'",sw)
checks={
 'three_modes': all(x in js for x in ["data-applicability-mode=\"all\"","data-applicability-mode=\"exact\"","data-applicability-mode=\"genus\""]),
 'ibera_guard': "species==='ibera'" in js,
 'exact_only': "a.level==='exact'" in js,
 'genus_includes_exact': "a.level==='exact'||a.level==='genus'" in js,
 'excludes_broader_mismatch_by_design': '같은 속 다른 종·DB 항목이 더 넓은 경우·적용성 미구조화 항목은 포함하지 않는다.' in js,
 'default_all': "mode:'all'" in js,
 'display_only_disclaimer': '표시만 좁히며 판정·순위·급여량을 다시 계산하지 않는다.' in js,
 'hidden_unchecked': 'unselect(label)' in js and 'label.hidden=!show' in js,
 'empty_disclaimer': '위험하거나 부적합하다는 뜻이 아니다' in js,
 'quick_mode_intersection': 'externalAllowed(label)' in fresh and 'tfd:applicability-filter-changed' in fresh,
 'global_filter_api': 'window.TFDCandidateApplicability' in js and 'allows' in js,
 'cache_current_enough': bool(m) and int(m.group(1))>=51 and int(m.group(2))>=20,
}
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
failed=[k for k,v in checks.items() if not v]
if failed: raise SystemExit('Applicability filter audit failed: '+', '.join(failed))
print('Applicability filter audit PASS')
