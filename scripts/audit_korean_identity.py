from pathlib import Path
R=Path(__file__).resolve().parents[1]
import json,re
files={p:(R/p).read_text(encoding='utf-8') for p in ['plant/mallow/index.html','plant/sowthistle/index.html','plant/clover/index.html','docs/EVIDENCE_EXPANSION_7_KOREAN_IDENTITY.md','scripts/generate_static_pages.py','data/curated_identity_notes.json']}
registry=json.loads((R/'data/public_assessments.json').read_text(encoding='utf-8'))
registry=registry if isinstance(registry,list) else registry.get('assessments',[])
mallow_verdict=next(a['verdict'] for a in registry if a['plant_id']=='mallow' and a.get('assessment_scope')!='exact_species')
checks={
 'mallow_exact_korean_identity':'Malva verticillata' in files['plant/mallow/index.html'],
 'mallow_not_auto_parviflora':'Malva parviflora' in files['plant/mallow/index.html'] and ('서로 다른 종' in files['plant/mallow/index.html'] or '직접 적용하지 않는다' in files['plant/mallow/index.html']),
 # The mallow grade comes only from the canonical registry; identity resolution never upgrades it,
 # and the unresolved Korean retail mapping stays a strong warning next to the grade.
 'mallow_verdict_follows_registry':f'data-verdict="{mallow_verdict}"' in files['plant/mallow/index.html'] and 'data-identity="alert"' in files['plant/mallow/index.html'],
 'sowthistle_korean_identity':'Sonchus oleraceus' in files['plant/sowthistle/index.html'],
 'sowthistle_distinguishes_asper':'Sonchus asper' in files['plant/sowthistle/index.html'],
 'sowthistle_genus_evidence_limit':'Sonchus sp.' in files['plant/sowthistle/index.html'] and ('직접섭식 증거로 승격하지 않음' in files['plant/sowthistle/index.html'] or '관찰종이 정확히' in files['plant/sowthistle/index.html']),
 'clover_exact_term_identity':'Trifolium repens' in files['plant/clover/index.html'],
 'clover_generic_warning':'일반명 ‘클로버’' in files['plant/clover/index.html'],
 'clover_genus_evidence_limit':'Trifolium sp.' in files['plant/clover/index.html'] and '종 수준 직접근거로 바꾸지 않는다' in files['plant/clover/index.html'],
 'curated_identity_notes_generated':'curated_identity_notes.json' in files['scripts/generate_static_pages.py'] and all(k in json.loads(files['data/curated_identity_notes.json'])['notes'] for k in ('mallow','sowthistle','clover')),
 'identity_not_safety_rule':'Identity resolution alone never upgrades a feeding verdict' in files['docs/EVIDENCE_EXPANSION_7_KOREAN_IDENTITY.md'],
}
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
failed=[k for k,v in checks.items() if not v]
if failed: raise SystemExit('Korean identity audit failed: '+', '.join(failed))
print('Korean identity audit PASS')
