from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
js=(ROOT/'ibera-direct-evidence-v56.js').read_text(encoding='utf-8')
assert 'ibera_direct_feeding_evidence_v56.json' in js
assert '이베라 야생 직접 섭식 근거' in js
assert '사육 급여 비율·매일 급여·무제한 안전성을 뜻하지 않는다' in js
assert "identity_scope==='exact_species'" in js
assert '속 수준으로만 확인됐다' in js
assert '원 연구 확인' in js
pages=list((ROOT/'plant').glob('*/index.html'))
assert pages
missing=[str(p.relative_to(ROOT)) for p in pages if 'ibera-direct-evidence-v56.js' not in p.read_text(encoding='utf-8')]
assert not missing, f'missing enhancer on {len(missing)} pages: {missing[:5]}'
print(f'OK: public direct-Ibera evidence enhancer present on {len(pages)} plant pages')
