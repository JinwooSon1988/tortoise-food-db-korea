from pathlib import Path
import json, re, sys

ROOT=Path(__file__).resolve().parents[1]
plants=json.loads((ROOT/'data/plants.json').read_text(encoding='utf-8'))
assessment_files=[ROOT/'data/assessments.json']+sorted((ROOT/'data').glob('assessments_korea_addendum*.json'))
assessments=[]
for path in assessment_files:
    assessments.extend(json.loads(path.read_text(encoding='utf-8')))
assessed_ids={a['plant_id'] for a in assessments}
errors=[]

for p in plants:
    pid=p['id']
    path=ROOT/'plant'/pid/'index.html'
    if not path.exists():
        errors.append(f'{pid}: detail page missing'); continue
    text=path.read_text(encoding='utf-8')
    if '식물동정' not in text: errors.append(f'{pid}: identity warning missing')
    if not any(x in text for x in ('현재 근거의 한계','근거의 한계와 해석 주의')) and pid not in {'mallow'}: errors.append(f'{pid}: evidence-limit card missing')
    verdicts=re.findall(r'(🟢|🟡|⚪|🔴)',text)
    if not verdicts: errors.append(f'{pid}: public verdict marker missing')
    if pid not in assessed_ids and pid!='mallow' and ('🟢' in verdicts or '🟡' in verdicts or '🔴' in verdicts):
        errors.append(f'{pid}: unassessed plant must remain hold/unresolved')
    if pid=='mallow':
        separated=('Malva parviflora' in text and ('서로 다른 종' in text or '자동' in text or '직접 적용하지 않는다' in text))
        if not separated: errors.append('mallow: explicit M. parviflora non-transfer warning missing')
        if '⚪' not in verdicts: errors.append('mallow: must remain hold/unresolved')

if errors:
    print('FAIL: verdict card audit')
    for e in errors: print('-',e)
    sys.exit(1)
print(f'PASS: {len(plants)} verdict cards follow safety invariants across {len(assessment_files)} assessment files')
