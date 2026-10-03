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
'아래 내용은 특정 종에서 확인된 별도 근거다. 이 내용을 다른 육지거북 종에 자동으로 적용하지 않는다.':'The following is separate evidence confirmed for a specific species. Do not automatically transfer it to other tortoise species.',
'먹이기 전에 식물부터 확인하세요':'Identify the plant before feeding',
'왜 이런 결론이 나왔을까?':'Why did we reach this conclusion?',
'현재 근거의 한계':'Limits of the current evidence',
'이 판정으로 말할 수 없는 것':'What this assessment cannot establish',
'이 근거가 지지하는 내용':'What this evidence supports',
'이 근거만으로 말할 수 없는 내용':'What this evidence alone cannot establish',
'직접 근거':'Direct evidence',
'전문 사육 근거':'Specialist husbandry evidence',
'근연 분류군 근거':'Related-taxon evidence',
'성분 근거':'Composition evidence',
'근거 수준':'Evidence level',
'신뢰도':'Confidence',
'판정 핵심':'Assessment summary',
'근거 구성':'Evidence composition',
'근거 적용범위':'Evidence applicability',
'실제 적용 원칙':'Practical application rule',
'야생 섭식 기록':'Wild feeding record',
'이 기록이 뜻하는 것':'What this record shows',
'이 기록만으로 말할 수 없는 것':'What this record cannot establish',
'야생에서는 실제로 어떻게 먹었나?':'How was it actually eaten in the wild?',
'검증된 영양성분 자료':'Verified nutrient data',
'더 깊이 보고 싶다면 — 학술자료와 원논문':'Go deeper — academic studies and original sources'
}.items():
    if ko in g and (ko not in lang or en not in lang): errors.append("missing detail translation: "+ko)
core_detail_copy={
'먹이기 전에 식물부터 확인하세요':'Identify the plant before feeding',
'왜 이런 결론이 나왔을까?':'Why did we reach this conclusion?',
'현재 근거의 한계':'Limits of the current evidence',
'대상 범위':'Scope',
'식물 분류':'Plant taxonomy',
'대상 동물':'Target animal',
'식물 부위·상태':'Plant part / state',
'연구 대상':'Study subject',
'식물·부위':'Plant / part',
'근거 직접성':'Evidence directness',
'근거 읽는 법':'How to read the evidence',
'원문/초록 열기':'Open source / abstract',
'육지거북에게 먹여도 되는지 현재 확인된 근거로 판정한다.':'Assesses whether this plant can be fed to tortoises using currently verified evidence.'
}
for ko,en in core_detail_copy.items():
    if ko in g and (ko not in lang or en not in lang): errors.append("missing core detail copy translation: "+ko)
for n in [
    'This plant has a reviewed evidence record.',
    'Reviewed evidence is available.',
    'evidence-deep',
    '영양성분은 참고자료로 확인하세요',
    'evsummary',
    'species-specific',
    'speciesexception'
]:
    if n not in g: errors.append("generator missing deep-detail bilingual/evidence contract: "+n)
for n in [
    'This section explains the evidence behind the conclusion.',
    'Direct evidence</b> addresses the target question directly.',
    'Indirect evidence</b> comes from other animals or related plants'
]:
    if n not in g: errors.append("generator missing complete English evidence explanation: "+n)
if 'en_pending="Evidence review is incomplete.' in g:
    errors.append("assessed pages may still hard-code incomplete English review state")
for n in ['function toggleEvidence(lang)',"document.querySelectorAll('.ko-evidence')","document.querySelectorAll('.en-evidence')"]:
    if n not in lang: errors.append('language toggle missing evidence-body switching: '+n)
if errors:
 print("FAIL: bilingual generated plant detail contract")
 for e in errors: print("-",e)
 sys.exit(1)
print("PASS: generated plant pages inherit bilingual UI contract")
