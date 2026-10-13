# 급여 판정 변경안 9건 검토표 (2026-10-13)

`docs/FEEDING_VERDICT_EVIDENCE_WEAKNESS_20261012.md`에서 제안한 변경안 9건을 연결된 출처 원문과 다시 대조했다. 원문은 2026-10-13에 직접 열어 확인했다.

- **이 PR에 넣은 것 (5건):** 근거 확실성만 낮추는 변경. 급여 등급(A–D)과 판정 문구는 그대로다.
- **넣지 않은 것 (4건):** 급여 등급이 바뀌는 변경. 원문을 확인한 결과 방향을 정할 근거가 부족하거나 새로 확인할 자료가 나와 검토 대상으로만 남겼다.
- 이 PR은 사용자 승인 전에는 main에 병합하지 않는다.

용어: 급여 등급은 `verdict`에서 나오는 A–D이고, 근거 확실성은 `confidence`(B = 중간, C+ = 다소 낮음, C = 낮음, C- = 매우 낮음)다. 둘은 별개다.

## 1. 이 PR에 넣은 변경 (근거 확실성만 변경)

| 식물 | 급여 등급 (변경 없음) | 근거 확실성 변경 | 변경 사유 | 원문에서 확인한 내용 | 근거의 적용 범위 | 불확실성 |
|---|---|---|---|---|---|---|
| 헤지머스터드 `hedgemustard` (Sisymbrium officinale) | B · 조건부 급여 (`limited_mixed_diet`) | B(중간) → C+(다소 낮음) | 연결된 육지거북 자료가 전문 사육자료 2곳뿐이고 육지거북 연구가 없다. 전문 사육자료 2곳이 연결된 판정 19건 중 B는 이 변경 대상 4건뿐이고, 나머지 15건은 B- 1, C+ 8, C 5, C- 1이다. | The Tortoise Table 712: "should be fed in moderation as it contains goitrogens". Tortoise Trust 야생 먹이 목록: "Hedge mustard (Sisymbrium officinale) young plants". 나머지 2건은 Kew 분류 페이지와 사람 식품 성분 논문이다. | 종 수준 일치. 대상 동물은 육지거북 일반. Tortoise Trust는 어린 식물체만 언급한다. | 급여시험이 아니다. 갑상선 영향 용량이나 안전 비율은 어느 자료에도 없다. Kew 페이지는 자동 접근이 차단돼 이번에 다시 열어 보지 못했다. |
| 흰광대나물 `lamium_album` (Lamium album) | A · 우선 권장 (`supported_mixed_diet`) | B → C+ | 위와 같음. 전문 사육자료 2곳이 근거의 전부다. | The Tortoise Table 774: "safe to feed and plant in the tortoise enclosure". Tortoise Trust 목록: "White-Dead Nettle (Lamium album)". | 종 수준 일치. 육지거북 일반. | 급여시험이 아니다. Tortoise Trust는 급여 부위를 밝히지 않는다. 장기 급여 비율 자료가 없다. |
| 살갈퀴 `vicia_sativa` (Vicia sativa) | B · 조건부 급여 (`limited_mixed_diet`) | B → C+ | 위와 같음. 두 번째 자료는 종자 혼합 안내서로, 급여 안전성을 평가한 자료가 아니다. | The Tortoise Table 310: "The flowers and leaves of this plant, although high in protein, are fine as a small part of a varied diet. The seeds contain cyanogenic glycoside … so avoid the pods", Common Vetch = Vicia sativa 명시. 종자 재배 안내 PDF: "Common Vetch - Vicia sativa 5%". | 종 수준 일치. 잎과 꽃에만 해당하고 씨앗·꼬투리는 제외. | 급여시험이 아니다. 종자 혼합 비율은 거북이 실제 먹는 양이나 안전성을 보여 주지 않는다. |
| 등갈퀴나물 `vicia_cracca` (Vicia cracca) | B · 조건부 급여 (`limited_mixed_diet`) | B → C+ | 위와 같음. 두 번째 자료는 상업용 종자 혼합 제품 페이지다. | The Tortoise Table 310: 위와 같은 문장, Tufted Vetch = Vicia cracca 명시. Naturescape NT Tortoise Food Mix: Vicia cracca 3%, Vicia sativa 7%, 21종 혼합. | 종 수준 일치. 잎과 꽃에만 해당. | 급여시험이 아니다. 판매 제품의 구성표는 독립된 전문 평가로 보기 어렵다. |
| 메밀잎 `buckwheatleaf` (Fagopyrum esculentum) | D · 급여 제외 (`do_not_feed`) | C(낮음) → C-(매우 낮음) | 연결된 근거가 식물 성분 논문 1건뿐이고 육지거북 자료가 없다. 같은 조건의 급여 제외 판정(마시멜로우, 키위잎)은 C-다. 또 아래 근거 레코드 오류를 바로잡으면 논문이 뒷받침하는 범위가 기존 설명보다 좁다. | PMC6617123(Habtemariam 2019, Antioxidants 8:160): 영국산 메밀의 잎과 꽃에서 루틴과 파고피린을 측정. "The fagopyrin content detected in the leaves in this investigation is very low … but whether this level could be associated with toxic effect in humans still remains to be established". | 식물 종은 일치. 동물 자료가 아니라 성분 분석이다. | 잎에서 파고피린이 검출됐다는 사실만 확인된다. 육지거북에서 광감작이 일어나는 양은 알 수 없다. 급여 제외는 근거가 부족한 상태에서의 보수적 판정이다. The Tortoise Table에는 메밀 항목이 없다(검색 결과 없음). |

### 함께 고친 근거 레코드 오류

`buckwheat_leaf_fagopyrin_2019`의 제목이 연결된 논문과 달랐다.

| 항목 | 수정 전 | 수정 후 |
|---|---|---|
| `source_title` | Fagopyrins and flavonoids in common and Tartary buckwheat sprouts and plants | Antioxidant and Rutin Content Analysis of Leaves of the Common Buckwheat (Fagopyrum esculentum Moench) Grown in the United Kingdom: A Case Study |
| `supports` | 녹색 지상부의 파고피린을 분석으로 규명했다는 설명 | 잎과 꽃에서 루틴·파고피린을 측정했고, 잎의 파고피린은 저자 표현으로 매우 낮으며 꽃보다 여러 배 낮다는 설명 |
| `plant_part_state` | green plant material / leaves and developmental plant material analyzed for fagopyrins | leaves and flowers analyzed for rutin and fagopyrins |

DOI(10.3390/antiox8060160), PMID(31163698), URL은 원래 이 논문을 가리키고 있어 그대로 두었다. 수정 전 제목의 논문은 이 DOI와 다른 문헌이며, 이번에 확인하지 않았다.

## 2. 넣지 않고 검토 대상으로 남긴 변경안 (급여 등급이 바뀌는 4건)

| 식물 | 현재 | 원래 변경안 | 원문에서 확인한 내용 | 확정하지 않은 이유 | 결정에 필요한 것 |
|---|---|---|---|---|---|
| 왕포아풀 `meadowgrass` (Poa pratensis) | B · 조건부 급여, 확실성 C | 판정 보류 | 연결된 근거 2건은 같은 Kew POWO 페이지이고 육지거북 자료가 아니다. 이 페이지는 자동 접근이 차단돼 '동물 먹이로 이용' 기록을 이번에 확인하지 못했다. The Tortoise Table에는 Poa 항목이 없다. 다만 같은 DB가 김의털속, 큰조아재비, 개밀 등 다른 벼과 풀은 'Safe to Feed'로 분류한다. | 직접 근거가 없다는 점은 확인됐다. 그러나 보류로 바꿀지, 벼과 풀 일반 근거를 연결해 현재 등급을 유지하고 확실성만 낮출지는 근거로 정해지지 않는다. | Poa pratensis를 다룬 육지거북 자료가 있는지 조사. 없으면 보류와 '등급 유지 + 확실성 C-' 중 선택. |
| 비름 `amaranthleaf` (Amaranthus spp., 국내 매핑 A. mangostanus) | C · 제한 급여, 확실성 C | 판정 보류 | 연결된 근거는 식물 성분 논문 1건(DOI 페이지가 자동 접근을 차단해 이번에 다시 열지 못함). 새로 확인한 자료: The Tortoise Table 521은 줄맨드라미(Amaranthus caudatus)를 'Do not Feed'로 분류하고 질산염 축적과 옥살산을 이유로 든다. | 전문 사육자료가 같은 속의 한 종을 급여 제외로 분류하므로, 보류가 아니라 더 엄격한 판정이 맞을 수 있다. 반면 그 자료는 관상용 A. caudatus만 다루며 국내 식용 비름과 같은 종이 아니다. 근연종 자료를 직접 근거처럼 쓸 수 없어 방향을 정하지 못했다. | 식용 비름(A. tricolor / A. mangostanus) 잎을 다룬 육지거북 자료 조사. 그때까지 현재 판정을 둘지 보류할지 결정. |
| 콩잎 `soybeanleaf` (Glycine max) | C · 제한 급여, 확실성 C | 판정 보류 | 연결된 근거는 곤충 사료 연구와 잎 성분 연구다(이번에 원문을 다시 열지 않았다). 새로 확인한 자료: The Tortoise Table 812는 콩나물·숙주(Vigna radiata; Glycine max)를 'Do not Feed'로 분류하며 이유는 높은 단백질과 피트산이다. 콩잎 항목은 없다. | 콩나물 자료는 부위가 달라 잎에 그대로 적용할 수 없다. 현재 판정 문구도 '주식으로 쓰지 않고 소량만'으로 이미 제한적이어서, 보류로 바꾸는 것이 더 정확한지는 근거로 정해지지 않는다. | 콩잎을 다룬 육지거북·초식 파충류 자료 조사. 없으면 보류와 현 판정 유지 중 선택. |
| 아욱 `mallow` (Malva spp., 국내 매핑 M. verticillata) | C · 제한 급여, 확실성 C- | 아욱잎과 같은 A · 우선 권장, 확실성 C로 통일 | The Tortoise Table 363: Safe to Feed, "All tortoises enjoy a snack on mallow flowers and leaves" (Malva spp.). Tortoise Trust 목록: "Mallows (Malva spp.)". Leone(Garden State Tortoise): 아욱류를 지중해 육지거북의 주식 식물 예로 든다. | 세 자료 모두 속 수준이고 M. verticillata를 이름으로 다루지 않는다. 두 기록의 판정이 다른 것은 사실이지만, 통일하려면 한쪽 급여 등급이 C에서 A로 오르거나 A에서 C로 내려간다. 속 수준 자료만으로 등급을 올리는 것은 확정하기 어렵다. 또 `mallow`의 현재 표시에 맞춰진 검사(`audit_blog_search_links.py`)가 있어 다른 작업 영역과 조율이 필요하다. | M. verticillata를 직접 다룬 자료 조사, 또는 두 기록 중 어느 쪽을 기준으로 할지 결정. |

## 3. 확인하지 못한 것

- Kew POWO 페이지(헤지머스터드, 왕포아풀)는 Cloudflare 차단으로 열지 않았다.
- 비름·콩잎에 연결된 논문 3건은 이번 검토에서 원문을 다시 열지 않았다. 레코드의 요약을 그대로 인용했다.
