from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
g=(ROOT/"scripts/generate_static_pages.py").read_text(encoding="utf-8")
lang=(ROOT/"language-toggle.js").read_text(encoding="utf-8")
errors=[]
for n in ['language-toggle.js?v=20260926-2','class="topmeta"']:
    if n not in g: errors.append("generator missing "+n)
for ko,en in {
'← 거북밥 DB 검색으로':'← Back to Tortoise Food DB search',
'판정 해석:':'Assessment interpretation:',
'식단 내 역할':'Role in the diet',
'식물 이름':'Plant names',
'학명 표기':'Scientific name',
'이 판정 공유하기':'Share this assessment',
'링크 복사':'Copy link',
'다른 먹이 찾기 →':'Find another food →'
}.items():
    if ko in g and (ko not in lang or en not in lang): errors.append("missing detail translation: "+ko)
if errors:
 print("FAIL: bilingual generated plant detail contract")
 for e in errors: print("-",e)
 sys.exit(1)
print("PASS: generated plant pages inherit bilingual UI contract")
