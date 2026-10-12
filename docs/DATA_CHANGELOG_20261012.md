# 수정 전후 데이터 비교 기록 (2026-10-12)

기준 커밋: `55a0a9d5` (main). 급여 판정·등급·신뢰도와 검증 영양수치(공개 표시값)는 바꾸지 않았다.

## 1. 값이 바뀐 데이터

| 파일 | 위치 | 수정 전 | 수정 후 | 근거 |
|---|---|---|---|---|
| `data/rda_food_composition_v56.json` | beetgreens (F095000B140a) `values_per_100g` | water_g 93.9, fiber_g 2.9, calcium_mg 79, phosphorus_mg 55 | water_g 92.9, calcium_mg 57, phosphorus_mg 54 (fiber_g 삭제) | RDA 10.4 '비트, 잎, 생것' 상세 화면. 원문에 식이섬유 값이 없다. 이전 값은 같은 기록의 `correction.previous_values_per_100g`에 보존 |
| `data/plant_nutrition_reference_v1.json` | `international-20261010-1`, `international-20261010-2` | `plant_id: waterdropwort` | `plant_id: minari`, `legacy_plant_ids: [waterdropwort]` | 두 ID는 같은 식물이며 공개 목록은 minari 카드를 표시한다. 수치·출처는 그대로 |
| `data/international_nutrition_reference_queue_20261010.json` | 미나리 대기열 항목 | `plant_id: waterdropwort` | `plant_id: minari`, `legacy_plant_ids: [waterdropwort]` | 위 참고자료 이전과 맞춤 |
| `data/plant_nutrition_v56.json` (8건), `data/plant_nutrition_reference_v1.json` (7건), `data/global_source_registry_v1.json`, `data/international_nutrition_crosscheck_shepherdspurse_20261010.json` | 농촌진흥청 CSV 출처 URL | `https://www.data.go.kr/data/15100065/fileData.do` (404) | `https://www.data.go.kr/data/15100065/standard.do` | 이전 주소가 '페이지를 찾을 수 없습니다'로 열린다. 같은 데이터셋의 현재 주소로 교체. 수치는 그대로 |
| `data/plants.json` | minari `aliases` | `["water dropwort"]` | `["water dropwort", "미나리잎"]` | waterdropwort의 별칭을 대표 기록에 병합 |
| `data/plants.json` | wheatleaf `aliases` | `["밀싹"]` | `["밀 잎"]` | '밀싹'은 다른 기록(wheatgrass)의 대표 이름 |
| `data/plants.json` | barleyleaf `aliases` | `["보리싹"]` | `["보리 잎"]` | '보리싹'은 barleygrass의 대표 이름 |
| `data/plants.json` | oatleaf `aliases` | `["귀리싹"]` | `["귀리 잎"]` | '귀리싹'은 oatgrass의 대표 이름 |
| `data/plants.json` | beanleaf `aliases` | `["콩잎"]` | `["강낭콩 잎"]` | '콩잎'은 soybeanleaf(대두 잎)의 대표 이름 |

## 2. 재생성된 파일

| 파일 | 달라진 내용 |
|---|---|
| `plant/minari/index.html` | '다른 이름'에 미나리잎 추가 |
| 국문·영문 상세 페이지 각 8개(애호박, 냉이, 다채, 아욱잎, 브로콜리새싹, 콩잎, 고구마줄기, 비름) | 영양자료 출처 링크 주소만 변경 |
| `plant/wheatleaf/index.html`, `plant/barleyleaf/index.html`, `plant/oatleaf/index.html`, `plant/beanleaf/index.html` | '다른 이름' 문구만 변경 |
| `data/nutrition_coverage_audit_v1.json` | minari가 `reference_only`로 분류, waterdropwort에 `legacy_alias_of: minari` 표시, `legacy_alias_ids`·`unique_identities` 항목 추가 |

페이지 생성기(`generate_static_pages.py`, `generate_en_pages.py`)는 수정하지 않고 실행만 했다. 위 21개 파일 외의 페이지는 바뀌지 않았다.

## 3. 영양자료 연결 수치

| 기준 | 검증자료 | 참고자료만 | 연결 없음 |
|---|---|---|---|
| 수정 전: 기록 182건 | 63 | 49 (waterdropwort 포함, minari 제외) | 70 (minari 포함) |
| 수정 후: 기록 182건 | 63 | 50 (minari, waterdropwort 모두) | 69 |
| 수정 후: 고유 식물 181종 (공개 목록 표시 기준) | 63 | 49 | 69 |

공개 목록은 미나리를 카드 하나로 보여 준다. 수정 전에는 그 카드가 '연결 없음'이었고 수정 후에는 '참고자료 있음'이다.

## 4. 새로 추가한 파일

| 파일 | 내용 |
|---|---|
| `data/plant_identity_registry_v1.json` | 중복·부위 구분·분류군 중첩·이름 충돌·학명 차이에 대한 결정 기록 |
| `data/plant_taxonomy_audit_v1.json` | 182개 학명의 GBIF / Kew WCVP / WFO 대조 결과 |
| `data/nutrition_verified_source_check_v1.json` | 검증자료 76건, 수치 843개의 원문 대조 원장 |
| `data/feeding_evidence_strength_audit_v1.json` | 급여 판정 186건의 근거 직접성 분류 |
| `scripts/build_plant_taxonomy_audit_v1.py` | 분류학 대조 도구 |
| `scripts/verify_verified_nutrition_sources_v1.py` | 검증자료 원문 대조 도구 |
| `scripts/build_feeding_evidence_strength_audit_v1.py` | 근거 직접성 분류 도구 |
| `scripts/qa_plant_identity_v1.py`, `scripts/qa_nutrition_integrity_v1.py` | 재발 방지 테스트 |
| `.github/workflows/plant-data-integrity-qa.yml` | 위 테스트를 PR과 main 푸시에서 실행 |
| `docs/PLANT_IDENTITY_TAXONOMY_AUDIT_20261012.md` 외 3건 | 보고서 |

## 5. 수정한 스크립트

| 파일 | 변경 |
|---|---|
| `scripts/build_nutrition_coverage_audit_v1.py`, `scripts/audit_nutrition_coverage.mjs` | 레지스트리의 중복 ID가 대표 ID의 영양자료 등급을 따르도록 처리. 기존 검사 항목은 그대로 |
| `scripts/audit_nutrition_v56.py`, `scripts/build_nutrition_reference_batch_20261010.py` | 농촌진흥청 CSV 기록이 인용해야 하는 데이터셋 주소를 현재 주소로 변경(검사 강도는 그대로) |
| `scripts/verify_nutrition_reference_sources_v1.py` | Feedipedia의 계산값 표시 `*`를 기록의 `equation`과 같은 뜻으로 비교(수치 비교 규칙은 그대로) |

## 6. 바꾸지 않은 것

- 급여 판정, 신뢰도, 근거 연결: 변경안은 `docs/FEEDING_VERDICT_EVIDENCE_WEAKNESS_20261012.md`에 제시만 했다.
- 식물 학명과 표시 이름: 자료별 차이는 기록만 했다.
- `plants.json`의 `waterdropwort` 행, 두 미나리 상세 페이지, 사이트맵, canonical 태그, 가이드 페이지, 검색·목록 화면 코드.
