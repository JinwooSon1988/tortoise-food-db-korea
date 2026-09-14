from pathlib import Path
import re
R=Path(__file__).resolve().parents[1]
js=(R/'candidate-applicability-summary.js').read_text(encoding='utf-8')
profile=(R/'profile-context.js').read_text(encoding='utf-8')
sw=(R/'sw.js').read_text(encoding='utf-8')
m=re.search(r"const CACHE='tfd-v(\d+)-stable-(\d+)'",sw)
checks={
 'today_only':"/\\/today\\/?(?:index\\.html)?$/" in js,
 'loads_plants':'../data/plants.json' in js,
 'loads_assessments':'../data/assessments.json' in js,
 'loads_evidence':'../data/evidence.json' in js,
 'loads_frequency':'../data/wild_observation_frequency.json' in js,
 'strict_ibera_primary':"subspecies_direct_wild_diet" in js and 'Testudo graeca ibera' in js,
 'exact_species_label':'정확한 종 직접근거' in js,
 'genus_label':'속 수준 직접근거' in js,
 'entry_broader_label':'논문 기록이 DB 항목보다 좁음' in js,
 'different_species_label':'같은 속·다른 종 직접근거' in js,
 'mismatch_label':'분류군 직접일치 아님' in js,
 'unknown_is_explicit':'식물 수준 적용성 확인 필요' in js,
 'no_silent_upgrade':'정확한 종이 직접 관찰됐다고 확대하지 않는다' in js,
 'candidate_cards_only':"#candidates label.candidate" in js,
 'no_amount_claim':'급여량·배합률·영양완전성·건강효과' in js,
 'script_loaded':'candidate-applicability-summary.js' in profile,
 'script_cached':'candidate-applicability-summary.js' in sw,
 'cache_current_enough':bool(m) and int(m.group(1))>=51 and int(m.group(2))>=19,
}
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
failed=[k for k,v in checks.items() if not v]
if failed: raise SystemExit('Candidate applicability summary audit failed: '+', '.join(failed))
print('Candidate applicability summary audit PASS')
