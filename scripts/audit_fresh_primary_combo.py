from pathlib import Path
import re
R=Path(__file__).resolve().parents[1]
js=(R/'fresh-primary-mode.js').read_text(encoding='utf-8')
sw=(R/'sw.js').read_text(encoding='utf-8')
m=re.search(r"const CACHE='tfd-v(\d+)-stable-(\d+)'",sw)
checks={
 'combo_button':'freshCombo3' in js and '빠른 후보 3종 선택' in js,
 'quick_mode_guard':"state.enabled" in js and 'recentCount(x)===0' in js,
 'primary_only':'isPrimary(x)&&recentCount(x)===0' in js,
 'applicability_intersection':'externalAllowed(x)' in js,
 'loads_plants':'../data/plants.json' in js,
 'family_diversity':'familyFor' in js and 'families.has' in js,
 'max_three':'chosen.length===3' in js,
 'no_fallback_other_evidence':'부족한 수를 다른 근거 수준 식물로 자동 보충하지 않는다' in js,
 'unselect_before_select':'clearCandidateSelection()' in js,
 'dispatch_change':"dispatchEvent(new Event('change'" in js,
 'no_balance_claim':'급여량·배합률·영양완전성을 계산한 조합이 아니다' in js,
 'cache_current_enough':bool(m) and int(m.group(1))>=51 and int(m.group(2))>=20,
}
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
failed=[k for k,v in checks.items() if not v]
if failed: raise SystemExit('Fresh primary combo audit failed: '+', '.join(failed))
print('Fresh primary combo audit PASS')
