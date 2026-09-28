from pathlib import Path
import json, re, sys

ROOT=Path(__file__).resolve().parents[1]
all_plants=json.loads((ROOT/'data/plants.json').read_text(encoding='utf-8'))
assessment_files=[ROOT/'data/public_assessments.json']
assessments=json.loads(assessment_files[0].read_text(encoding='utf-8'))
if isinstance(assessments,dict): assessments=assessments.get('assessments',assessments.get('records',[]))
public_groups={'Mediterranean_Testudo','Tortoise_general','Herbivorous_reptile_general'}
assessed_ids={a['plant_id'] for a in assessments if a.get('species_group') in public_groups}
plants=[p for p in all_plants if p.get('identity_status')!='candidate_name' and p.get('id') in assessed_ids]
errors=[]

for p in plants:
    pid=p['id']
    path=ROOT/'plant'/pid/'index.html'
    if not path.exists():
        errors.append(f'{pid}: detail page missing'); continue
    text=path.read_text(encoding='utf-8')
    if '식물동정' not in text: errors.append(f'{pid}: identity warning missing')
    if not any(x in text for x in ('현재 근거의 한계','근거의 한계와 해석 주의')) and pid not in {'mallow'}: errors.append(f'{pid}: evidence-limit card missing')
    verdicts=re.findall(r'(?:A · 혼합식 활용 가능|B · 제한적 혼합 급여|C · 가끔 보조 급여|D · 급여하지 않음|판단보류 / [^<]+)',text)
    if not verdicts: errors.append(f'{pid}: public verdict marker missing')
    if pid=='mallow':
        separated=('Malva parviflora' in text and ('서로 다른 종' in text or '자동' in text or '직접 적용하지 않는다' in text))
        if not separated: errors.append('mallow: explicit M. parviflora non-transfer warning missing')
        if not any('판단보류' in x for x in verdicts): errors.append('mallow: must remain hold/unresolved')

if errors:
    print('FAIL: verdict card audit')
    for e in errors: print('-',e)
    sys.exit(1)
candidate_ids={p['id'] for p in all_plants if p.get('identity_status')=='candidate_name'}
for pid in candidate_ids:
    if (ROOT/'plant'/pid/'index.html').exists():
        print('FAIL: candidate detail page published',pid); sys.exit(1)
print(f'PASS: {len(plants)} non-candidate verdict cards follow safety invariants; {len(candidate_ids)} candidates withheld across {len(assessment_files)} assessment files')
