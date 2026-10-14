# 연구 DB 검증 6차: Feedipedia 표본 수 오류와 연구 공백 (2026-10-14)

브랜치 `research/feedipedia-nb-verification-20261014`(5차 브랜치 `e1c0b88a`에서 분기)에서 작업했다. 다른 작업자가 5차 브랜치의 같은 파일(`qa_global_plant_evidence_research_v5.py`, `forage_nutrition_exclusion_audit_v5.json`)을 같은 시간대에 수정하고 있어, 그 브랜치에 직접 올리지 않고 별도 브랜치로 분리했다. 급여 등급, 공개 데이터, UI, 번역은 바꾸지 않았다.

## 1. 원인

`scripts/verify_nutrition_reference_sources_v1.py`의 `parse_feedipedia`는 표를 평문으로 펴서 읽는다. 이 과정에서 빈 칸이 사라진다. 그래서 표본 수(Nb) 칸이 빈 행은 다음 행의 Nb를 자기 값으로 가져간다.

이 공용 파서는 공개 영양 작업에서도 쓰이므로 고치지 않았다. 대신 연구용 빌드(v2, v5)는 표의 행을 직접 읽는 별도 파서로 값마다 평균과 표본 수를 한 번 더 확인한다.

## 2. feedipedia-11865 (블랙메딕 *Medicago lupulina* 생초)

2026-10-14에 원문 페이지를 다시 받아 행을 직접 읽었다.

| 항목 | 원문 평균·단위 | 원문 Nb | 계산값 표시(*) | 이전 기록의 Nb | 그 Nb의 실제 출처 |
|---|---|---|---|---|---|
| 건물(dry matter) | 20.9 % as fed | 빈칸 | 없음 | 165 | 바로 아래 조단백질 행의 Nb |
| 칼슘 | 16.1 g/kg DM | 빈칸 | 없음 | 72 | 바로 아래 인 행의 Nb |

- **수정:** 표본 수가 없는 값은 넣지 않는다는 2차 빌드의 원래 규칙대로 두 값을 뺐다. 생성 스크립트(`build_global_plant_evidence_research_v2.py`)에 행 확인을 넣고 `--nutrition-only`로 영양 파일만 다시 만들었다. 2차 근거 파일은 다시 만들지 않았다(다른 작업자의 `a2dd8ed7` 정정을 보존하기 위해서다).
- **결과:** 2차 영양 값은 248개에서 246개가 됐다. 뺀 값은 기록의 `values_dropped_no_sample_count_on_page`에 원문 평균과 함께 남아 있다.
- **연쇄 수정:** 3차 `nutrient_safety_view_v3.json`에서 11865의 칼슘 값이 빠졌다. 인 값만 남아서 칼슘 대 인의 몫도 이 기록에는 없다.
- **빌드 결함 수정:** 3차 빌드를 다시 돌리면 3차 정정 파일의 '정정 전 수치'가 정정 후 값으로 덮어써지는 문제를 찾았다. 정정 전 수치를 2차 원본 전사본에서 읽도록 고쳤다. 정정 파일 내용은 바뀌지 않았다.

## 3. 같은 오류 전수 검사

`scripts/audit_feedipedia_sample_counts_v6.py`가 저장소의 모든 Feedipedia 값을 원문 76쪽과 대조한다. 결과는 `data/research/feedipedia_sample_count_audit_v6.json`(페이지별 sha256 포함)에 있다.

| 대상 | 값 | 결과 |
|---|---|---|
| 연구 영양 1·2·5차에 남아 있는 값 | 346 | 346 모두 평균·단위·Nb 일치 |
| 연구에서 뺀 값(2차 2, 5차 4) | 6 | 6 모두 원문 Nb 빈칸 |
| 공개 `plant_nutrition_dm_basis_v1.json`(Nb 저장) | 219 | 219 모두 일치 |
| 공개 `plant_nutrition_reference_v1.json`(Nb 미저장) | 498 | 평균 493 일치, 유채잎(15683) 5개는 페이지에 표가 여러 개라 자동 대조 불가 |

공개 파일은 읽기만 했다. 유채잎 5개 값은 공개 데이터 담당자가 직접 확인해야 한다.

## 4. 5차 제외 수치 4개

`forage_nutrition_exclusion_audit_v5.json`(다른 작업자가 만든 파일)의 네 행을 원문 행으로 확인했다. 키는 그대로 두고 확인 결과를 채웠다(`review_status: source_row_verified`).

| 표 | 항목 | 원문 평균·단위 | 원문 Nb | 계산값 표시 | 이전 Nb | 그 Nb와 같은 Nb를 가진 아래 행 |
|---|---|---|---|---|---|---|
| 12645 서브클로버 생초 | 마그네슘 | 1.7 g/kg DM | 빈칸 | 없음 | 6 | 칼륨 |
| 12645 | 나트륨 | 2.2 g/kg DM | 빈칸 | 없음 | 33 | 같은 표 안에서 찾지 못함 |
| 12646 서브클로버 건초 | 건물 | 90.2 % as fed | 빈칸 | 없음 | 6 | 조단백질 |
| 12646 | 조지방 | 2.2 % DM | 빈칸 | 없음 | 5 | 회분, ADF, 리그닌 |

- **제외 사유:** 네 값 모두 원문에 표본 수가 인쇄되어 있지 않다(`source_row_prints_no_sample_count`).
- **이전 표본 수:** 6, 33, 6, 5는 원문 확인값이 아니다. 나트륨의 33이 어디서 왔는지는 찾지 못했다.

## 5. 연구 공백 목록

`data/research/research_gap_register_v6.json`에 정리했다. 어떤 식물도 빼지 않았다.

**원문 미열람 인용 74건 (16개 문헌 묶음)**

| 상태 | 묶음 |
|---|---|
| 찾아보지 않음(단행본·학위논문 등) | 7 |
| 검색했으나 공개 전문 없음 | 3 |
| 6차에 검색했으나 원문을 찾지 못함 | 2 (Longepierre·Grenot 1999, Vijaya 1983) |
| 유료 | 1 |
| 호스트 차단(우회하지 않음) | 2 |
| 위치만 확인, 내려받기 실패 | 1 |

- **추가 확인:** 6차에서 새로 원문을 읽어 확인한 인용은 없다. 74건은 모두 '2차 인용, 확인된 관찰 아님'으로 남는다.
- **기록 내용:** 묶음마다 거북 종, 식물 이름, 같은 거북·식물에 대한 독립 1차 기록 유무를 적었다.

**미해소 학명 48개**

- 구성: 1~4차 46개, 5차 2개('Medicago saliva', 'Vicus bengalensis', 스캔 판독 불가)
- 이름마다 기록된 거북 종, 종 특정 여부, 식물 부위, 근거 종류를 적었다. 근거 종류는 직접 관찰, 분변·씨앗 검출, 사육 급여, 동물원·수의 지침, 사육단체, 2차 인용으로 나눈다.
- 학명은 확정하지 않았다.

## 6. 검증

- **스크립트:** `scripts/qa_global_plant_evidence_research_v6.py`를 새로 만들었다. 남은 Feedipedia 값이 모두 원문 행과 일치하는지, 뺀 값의 원문 Nb가 빈칸인지, 제외 감사의 확인 필드, 공백 목록의 누락을 검사한다. 음성 테스트 5개 모두 실패를 확인했다.
- **기존 QA:** 1~5차 QA도 모두 통과한다.
- **자동 실행:** `research-layer-qa.yml`의 v1~v9 반복이 이 스크립트를 자동 실행한다. 감사 스크립트와 공백 목록 스크립트가 바뀔 때도 실행되도록 경로를 추가했다.

## 7. 재현

```
python scripts/build_global_plant_evidence_research_v2.py --cache <GBIF 캐시> --feedipedia-cache <원문 저장 폴더> --offline --nutrition-only
python scripts/build_global_plant_evidence_research_v3.py --cache <GBIF 캐시> --wfo-cache <WFO 캐시> --offline
python scripts/build_global_plant_evidence_research_v5.py --cache <GBIF 캐시> --feedipedia-cache <원문 저장 폴더> --offline
python scripts/verify_forage_nutrition_v5.py --pages <원문 저장 폴더> --fetched-on 2026-10-14
python scripts/audit_feedipedia_sample_counts_v6.py --pages <원문 저장 폴더> --fetched-on 2026-10-14
python scripts/build_research_gap_register_v6.py
python scripts/qa_global_plant_evidence_research_v6.py
```
