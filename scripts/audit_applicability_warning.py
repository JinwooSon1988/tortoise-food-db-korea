from pathlib import Path
import re
R=Path(__file__).resolve().parents[1]
js=(R/'fresh-primary-combo-explain.js').read_text(encoding='utf-8')
sw=(R/'sw.js').read_text(encoding='utf-8')
m=re.search(r"const CACHE='tfd-v(\d+)-stable-(\d+)'",sw)
checks={
 'reads_db_scientific':'p?.scientific' in js,
 'uses_reported_taxon':'taxon_reported' in js,
 'detects_generic_taxa':'isGenericTaxon' in js and 'sp|spp' in js,
 'exact_species_label':'정확한 종 직접근거' in js,
 'genus_level_label':'속 수준 직접근거' in js,
 'broader_entry_warning':'논문 기록이 DB 항목보다 좁음' in js,
 'different_species_warning':'같은 속·다른 종 직접근거' in js,
 'no_species_upgrade':'정확한 종이 직접 관찰됐다고 확대하지 않는다' in js and '종 수준 직접근거로 취급하지 않는다' in js,
 'wild_not_ratio':'사육 급여비율이 아니다' in js,
 'no_nutrition_claim':'급여량·배합률·영양완전성·건강효과' in js,
 'cache_current_enough':bool(m) and int(m.group(1))>=51 and int(m.group(2))>=18,
}
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
failed=[k for k,v in checks.items() if not v]
if failed: raise SystemExit('Applicability warning audit failed: '+', '.join(failed))
print('Applicability warning audit PASS')
