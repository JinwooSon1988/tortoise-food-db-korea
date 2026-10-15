# 식물 동정·검색 정확성 검토 (2026-10-16)

결정 기록: `data/plant_identity_search_review_20261016.json` (필드별 수정 전·후 값, 이유, 읽은 원문).
적용 스크립트: `scripts/apply_plant_identity_search_review_20261016.py`. 필드가 아직 "수정 전" 값일 때만 쓰므로 다시 실행해도 이후 수정을 되돌리지 않는다.

급여 판정·등급·확실성, 근거 기록, 상세 URL은 바꾸지 않았다. *Cucurbita pepo* 식물이나 판정은 새로 만들지 않았다.

## 1. 애호박(*Cucurbita moschata*)과 주키니(*Cucurbita pepo*)

**문제:** `zucchini` 항목(애호박, *C. moschata* 어린 열매)의 별칭에 '주키니'와 'zucchini'가 있었다. 한국어 상세 페이지는 "다른 이름 · 주키니, zucchini", 영어 페이지는 "Also known as · zucchini"로 표시했다. 두 이름은 다른 종을 가리킨다.

**원문 (2026-10-16 열람):**
- The Tortoise Table, Courgette: https://www.thetortoisetable.org.uk/plant-database/viewplants/?plant=637
  - "Common Name: Courgette (Zucchini, Baby Marrow)", "Latin Name: Cucurbita pepo".
- The Tortoise Table, Squash (이 판정의 근거): https://www.thetortoisetable.org.uk/plant-database/viewplants/?plant=627
  - "Cucurbita spp. esp. Cucurbita pepo; Cucurbita maxima; Cucurbita moschata".
  - Zucchini는 *C. pepo* 아래, Butternut Squash는 *C. moschata* 아래에 나온다.
- 애호박 성분값은 농촌진흥청 식품성분표 `R106-198050001-0000`(호박_애호박_생것)이다. 저장소 기록이며 이번에 다시 열람하지 않았다. USDA FDC 169291(*C. pepo* zucchini)은 같은 이유로 이미 제외돼 있다(`scripts/qa_usda_nutrition_batch1_v1.py`).
- '주키니'는 zucchini의 외래어 표기다. 이 연결을 뒷받침하는 한국어 원문은 읽지 않았다.

**수정:**
- '주키니'·'zucchini'를 별칭에서 빼고, 검색 전용 용어(`search_aliases`)로 옮겼다. 기존 검색어로 계속 이 항목을 찾을 수 있다.
- 영어 카탈로그의 별칭 'zucchini'도 뺐다.
- 검색 이름 지도 두 파일(`korean_search_name_map_v1.json`, `korean_retail_name_map.json`)에서 애호박을 `name_candidate_only`로 표시했다. 상품명만으로 학명을 확정하지 않는 다른 10개 식물과 같은 방식이다. 이 표시로 한·영 상세 페이지에 식물동정 주의가 나온다.
- 식물동정 주의에 두 종의 차이를 적었다(`data/curated_identity_notes.json`, 영어 번역 4문장). 이 판정을 *C. pepo* 주키니에 적용하지 않고, 주키니는 따로 판정하지 않았다는 점도 밝혔다.

## 2. 미나리 `minari`와 `waterdropwort`

`waterdropwort`는 `minari`의 이전 ID다(`data/plant_identity_registry_v1.json`의 canonical_aliases). 등급(급여 제외)·확실성(C-)·근거 ID·이미지는 이미 같았다. 그러나 판정 설명(`why`), 한계(`limits`), 적용 범위(`applicability_note`), 영어 설명, 한국어 '다른 이름'이 달라서, 같은 식물의 두 주소가 서로 다른 설명을 보여 줬다.

대표 ID인 `minari`의 문구로 맞췄다. 수정 전 문구는 결정 기록에 남아 있다. 두 주소(`/plant/minari/`, `/plant/waterdropwort/`, 영어 포함)는 그대로 공개된다.

## 3. 자동 QA (`scripts/qa_plant_identity_v1.py`)

**새 검사:**
- **7번:** 한 분류군을 가리키는 이름(`taxon_bound_terms`: zucchini, courgette, 주키니 → *C. pepo*)을 다른 분류군 식물이 이름이나 별칭으로 표시하면 실패한다(한국어·영어 모두). 검색 전용 용어로 둘 수는 있지만, 그 경우 상세 페이지의 식물동정 주의가 다른 분류군을 밝혀야 한다.
- **8번:** 이전 ID와 대표 ID의 공개 판정 문구 전체, 영어 `why`·`role`이 다르면 실패한다.
- **9번:** 같은 학명이지만 부위를 나눈 기록(예: 애호박 열매와 애호박잎)이 같은 판정 설명을 공유하면 실패한다. 부위별 판정을 복사하지 못하게 막는다.

**음성 시험:** 시험 변조 7건을 모두 실패로 잡았다.
- 애호박에 '주키니' 별칭 복원
- 영어 별칭 'Zucchini' 복원
- 식물동정 주의만 삭제
- 오이에 'courgette' 별칭 추가
- 열매 설명을 잎에 복사
- 이전 ID 한계 문구 변경
- 이전 ID 영어 설명 변경

## 4. 바꾸지 않은 것과 남은 과제

**바꾸지 않은 것:**
- 애호박 열매(급여 제외, C)와 애호박잎(제한 급여, C)은 계속 별도로 판정한다.
- 호박잎·호박꽃(*Cucurbita* spp.)의 속 수준 기록도 그대로 둔다.

**남은 과제:**
- **`waterdropwort` 페이지의 canonical 태그와 sitemap (SEO 담당 결정):** 지금은 자기 자신을 canonical로 가리키고 sitemap에도 실려 있다. 이제 내용이 `minari`와 같아졌으므로, canonical을 `minari`로 바꾸거나 sitemap에서 빼는 방안을 검토할 수 있다.
- **영어 홈 검색의 식물동정 주의:** 한국어 홈 검색에만 있고 영어 홈 검색에는 없다. 이번 변경 전부터 그랬다(UI 담당).
- **'돌미나리':** 검색 결과가 없다. 별칭 추가 근거를 확인하지 않아 넣지 않았다.
