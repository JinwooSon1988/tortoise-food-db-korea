from pathlib import Path
R=Path(__file__).resolve().parents[1]
files={p:(R/p).read_text(encoding='utf-8') for p in ['plant/mallow/index.html','plant/sowthistle/index.html','plant/clover/index.html','scripts/generate_static_pages.py','docs/EVIDENCE_EXPANSION_7_KOREAN_IDENTITY.md']}
checks={
 'mallow_exact_korean_identity':'Malva verticillata' in files['plant/mallow/index.html'],
 'mallow_not_auto_parviflora':'Malva parviflora' in files['plant/mallow/index.html'] and ('서로 다른 종' in files['plant/mallow/index.html'] or '직접 적용하지 않는다' in files['plant/mallow/index.html']),
 'mallow_verdict_not_upgraded':'급여판정 보류' in files['plant/mallow/index.html'],
 'sowthistle_korean_identity':'Sonchus oleraceus' in files['plant/sowthistle/index.html'],
 'sowthistle_distinguishes_asper':'Sonchus asper' in files['plant/sowthistle/index.html'],
 'sowthistle_genus_evidence_limit':'Sonchus sp.' in files['plant/sowthistle/index.html'] and ('직접섭식 증거로 승격하지 않음' in files['plant/sowthistle/index.html'] or '관찰종이 정확히' in files['plant/sowthistle/index.html']),
 'clover_exact_term_identity':'Trifolium repens' in files['plant/clover/index.html'],
 'clover_generic_warning':'일반명 ‘클로버’' in files['plant/clover/index.html'],
 'clover_genus_evidence_limit':'Trifolium sp.' in files['plant/clover/index.html'] and '종 수준 직접근거로 바꾸지 않는다' in files['plant/clover/index.html'],
 'generator_persists_overrides':'IDENTITY_OVERRIDE' in files['scripts/generate_static_pages.py'] and 'Malva verticillata L.' in files['scripts/generate_static_pages.py'],
 'identity_not_safety_rule':'Identity resolution alone never upgrades a feeding verdict' in files['docs/EVIDENCE_EXPANSION_7_KOREAN_IDENTITY.md'],
}
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
failed=[k for k,v in checks.items() if not v]
if failed: raise SystemExit('Korean identity audit failed: '+', '.join(failed))
print('Korean identity audit PASS')
