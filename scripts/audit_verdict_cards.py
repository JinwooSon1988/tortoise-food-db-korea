from pathlib import Path
import json, re, sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from public_verdict import load_assessments, by_plant, representative, display, public_plants

ROOT=Path(__file__).resolve().parents[1]
all_plants=json.loads((ROOT/'data/plants.json').read_text(encoding='utf-8'))
assessments=load_assessments()
rows_by=by_plant(assessments)
evidence_by_id={e['id']:e for e in json.loads((ROOT/'data/public_evidence_records.json').read_text(encoding='utf-8')).get('records',[])}
plants=public_plants(all_plants,assessments)
errors=[]

for p in plants:
    pid=p['id']
    path=ROOT/'plant'/pid/'index.html'
    if not path.exists():
        errors.append(f'{pid}: detail page missing'); continue
    text=path.read_text(encoding='utf-8')
    g=display(representative(rows_by.get(pid,[])))
    species_only=[a for a in rows_by.get(pid,[]) if a.get('assessment_scope')=='exact_species' and a.get('animal_taxon') and any(evidence_by_id.get(eid,{}).get('source_type') in ('specialist_husbandry','captive_feeding_record','wild_feeding_observation','husbandry_recommendation') for eid in a.get('evidence_ids',[]))]
    if representative(rows_by.get(pid,[])) is None and species_only:
        label='급여 기록 있음 (검증 중)'
        meaning='특정 육지거북 종에 한정된 급여 관련 자료가 있습니다. 실제 섭식 관찰과 사육 지침의 권장은 서로 다른 근거이며, 전체 육지거북에 대한 안전성 등급은 확정되지 않았습니다.'
        if label not in text or meaning not in text:
            errors.append(f'{pid}: species-only feeding record label/meaning missing')
        if 'data-grade="보류"' not in text or 'data-verdict="none"' not in text:
            errors.append(f'{pid}: species-only evidence must remain ungraded')
    elif g['label'] not in text or g['meaning'] not in text:
        errors.append(f'{pid}: public verdict label/meaning missing')
    for legacy in ('🟢','🟡','🟠','🔴','⚪','판단보류 / '):
        if legacy in text: errors.append(f'{pid}: legacy verdict marker {legacy}')
    if pid=='mallow':
        separated=('Malva parviflora' in text and ('서로 다른 종' in text or '다른 종이다' in text or '직접 적용하지 않는다' in text))
        if not separated: errors.append('mallow: explicit M. parviflora non-transfer warning missing')
        if 'data-identity="alert"' not in text: errors.append('mallow: unresolved Korean retail mapping must show the strong identity warning')

if errors:
    print('FAIL: verdict card audit')
    for e in errors: print('-',e)
    sys.exit(1)
candidate_ids={p['id'] for p in all_plants if p.get('identity_status')=='candidate_name'}
for pid in candidate_ids:
    if (ROOT/'plant'/pid/'index.html').exists():
        print('FAIL: candidate detail page published',pid); sys.exit(1)
print(f'PASS: {len(plants)} non-candidate verdict cards follow safety invariants; {len(candidate_ids)} candidates withheld; canonical registry data/public_assessments.json')
