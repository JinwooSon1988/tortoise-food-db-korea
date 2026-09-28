from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
g=(ROOT/"scripts/generate_static_pages.py").read_text(encoding="utf-8")
lang=(ROOT/"language-toggle.js").read_text(encoding="utf-8")
errors=[]
for n in ['language-toggle.js?v=20260926-3','class="topmeta"','class="ko-evidence"','class="en-evidence"']:
    if n not in g: errors.append("generator missing "+n)
for ko,en in {
'← 거북밥 DB 검색으로':'← Back to Tortoise Food DB search',
'판정 해석:':'Assessment interpretation:',
'식단 내 역할':'Role in the diet',
'식물 이름':'Plant names',
'학명 표기':'Scientific name',
'이 판정 공유하기':'Share this assessment',
'링크 복사':'Copy link',
'다른 먹이 찾기 →':'Find another food →',
'종별 특이사항':'Species-specific notes',
'아래 내용은 특정 종에서 확인된 별도 근거다. 이 내용을 다른 육지거북 종에 자동으로 적용하지 않는다.':'The following is separate evidence confirmed for a specific species. Do not automatically transfer it to other tortoise species.'
}.items():
    if ko in g and (ko not in lang or en not in lang): errors.append("missing detail translation: "+ko)
for n in [
    'This plant has a reviewed evidence record.',
    'Reviewed evidence is available.',
    '학술자료와 원논문',
    '검증된 영양성분 자료',
    '근거 읽는 법',
    'quickfacts',
    'species-specific',
    'speciesexception'
]:
    if n not in g: errors.append("generator missing deep-detail bilingual/evidence contract: "+n)
if 'en_pending="Evidence review is incomplete.' in g:
    errors.append("assessed pages may still hard-code incomplete English review state")
for n in ['function toggleEvidence(lang)',"document.querySelectorAll('.ko-evidence')","document.querySelectorAll('.en-evidence')"]:
    if n not in lang: errors.append('language toggle missing evidence-body switching: '+n)
if errors:
 print("FAIL: bilingual generated plant detail contract")
 for e in errors: print("-",e)
 sys.exit(1)
print("PASS: generated plant pages inherit bilingual UI contract")
