from pathlib import Path
import json, re, sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from public_verdict import load_assessments, by_plant, representative, display, public_plants

ROOT=Path(__file__).resolve().parents[1]
all_plants=json.loads((ROOT/'data/plants.json').read_text(encoding='utf-8'))
assessments=load_assessments()
rows_by=by_plant(assessments)
plants=public_plants(all_plants,assessments)
errors=[]

for p in plants:
    pid=p['id']
    path=ROOT/'plant'/pid/'index.html'
    if not path.exists():
        errors.append(f'{pid}: detail page missing'); continue
    text=path.read_text(encoding='utf-8')
    g=display(representative(rows_by.get(pid,[])))
    if not re.search(r'data-identity="(alert|note)"',text) or '식물동정' not in text: errors.append(f'{pid}: plant-identity boundary missing')
    if '<h3>아직 확인되지 않은 내용</h3>' not in text: errors.append(f'{pid}: evidence-limit block missing')
    if '근거 부족 ≠ 안전' not in text: errors.append(f'{pid}: "근거 부족 ≠ 안전" principle missing')
    if g['label'] not in text or g['meaning'] not in text: errors.append(f'{pid}: public verdict label/meaning missing')
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
