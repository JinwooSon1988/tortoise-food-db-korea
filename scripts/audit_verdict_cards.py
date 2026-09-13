from pathlib import Path
import json, re, sys

ROOT=Path(__file__).resolve().parents[1]
plants=json.loads((ROOT/'data/plants.json').read_text(encoding='utf-8'))
assessments=json.loads((ROOT/'data/assessments.json').read_text(encoding='utf-8'))
med={a['plant_id']:a for a in assessments if a.get('species_group')=='Mediterranean_Testudo'}
errors=[]

for p in plants:
    pid=p['id']
    path=ROOT/'plant'/pid/'index.html'
    if not path.exists():
        errors.append(f'{pid}: detail page missing')
        continue
    text=path.read_text(encoding='utf-8')
    if '식물동정 주의' not in text:
        errors.append(f'{pid}: identity warning missing')
    if '현재 근거의 한계' not in text:
        errors.append(f'{pid}: evidence-limit card missing')
    verdicts=re.findall(r'(🟢|🟡|⚪)', text)
    if not verdicts:
        errors.append(f'{pid}: public verdict marker missing')
    if pid not in med and pid!='mallow' and '🟢' in verdicts:
        errors.append(f'{pid}: unassessed plant must not be green')
    if pid=='mallow':
        if 'Malva parviflora로 자동' not in text:
            errors.append('mallow: explicit Malva parviflora non-mapping warning missing')
        if '⚪' not in verdicts:
            errors.append('mallow: must remain hold/unresolved')

if errors:
    print('FAIL: verdict card audit')
    for e in errors:
        print('-',e)
    sys.exit(1)
print(f'PASS: {len(plants)} verdict cards follow safety invariants')
