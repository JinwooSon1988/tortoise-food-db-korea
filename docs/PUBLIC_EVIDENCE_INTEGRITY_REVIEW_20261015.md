# 공개 근거 무결성 점검 (2026-10-15)

대상은 공개 근거 기록 277건(`data/public_evidence_records.json`)과 판정 186건(`data/public_assessments.json`) 전부다.

- 결정 기록: `data/public_evidence_integrity_review_20261015.json`. 바꾼 항목마다 이유, 실제로 확인한 수준, 바꾸기 전 값을 적었다.
- 적용 스크립트: `scripts/apply_public_evidence_integrity_review_20261015.py`. 다시 실행해도 결과가 같다.
- 자동 QA: `scripts/qa_public_evidence_integrity_v1.py`. 결과는 `data/public_evidence_integrity_qa_v1.json`에 남는다.

이번 점검의 원칙은 다음과 같다.

- 기록은 하나도 지우지 않았다.
- 급여 등급(A–D)과 근거 확실성은 바꾸지 않았다. 바꿀 만한 경우는 7절에 제안으로만 적었다.
- 근거가 부족하다는 사실을 독성의 증거로 다루지 않았다.

## 1. 요약

| 항목 | 수정 전 | 수정 후 |
|---|---|---|
| 서로 다른 원문 수 (기록 277건 기준) | 원문 식별자 없음 | 259곳 (`source_id`) |
| 판정 하나가 같은 원문을 두 번 이상 인용 | 4건 (수영·버드나무·보리지·왕포아풀) | 같은 결과를 반복한 기록 5건은 대표 카드 하나로 합쳐 표시하고 1곳으로 센다. 서로 다른 결과 2건(버드나무 2020, 보리지 2025)은 카드를 유지하고 1곳으로 센다. |
| 검색·목록 페이지를 근거로 쓰는 기록 | 13건 | 0건 (식물별 페이지로 교체, 13건 모두 원문 확인) |
| 다른 논문을 가리키는 DOI | 2건 | 0건 |
| PubMed에 있는데 PMID가 빠진 논문 기록 | 9건 (1건은 DOI도 없음) | 0건 (PubMed에서 1:1로 확인된 것만 추가) |
| 원문이 다루지 않는 종을 대상으로 적은 기록 | 1건 (딸기) | 0건 |

화면에서 달라지는 점은 두 가지다.

- **출처 수:** 판정 화면의 "연결된 출처"는 이제 같은 원문을 1건으로 센다. 수영은 6건에서 3건, 보리지는 5건에서 3건, 버드나무잎은 5건에서 4건, 왕포아풀은 2건에서 1건이 됐다.
- **합친 카드 안내:** 한 카드로 합친 기록이 있으면 카드에 "같은 원문의 같은 결과를 담은 기록 N건을 이 카드 하나로 표시했습니다"라고 쓴다.

두 가지 모두 한국어·영어 화면에 같은 규칙으로 적용했다. 생성기 `generate_static_pages.py`와 `generate_en_pages.py`는 공통 모듈 `scripts/evidence_sources.py`를 쓴다.

## 2. 작업 1 — 같은 원문의 중복 기록

DOI, PMID, PMCID, 원문 URL, 논문 제목을 대조했다. DOI와 PMID의 대응은 NCBI E-utilities로 확인했다.

| 판정 | 원문 | 기록 | 원문 확인 수준 | 처리 |
|---|---|---|---|---|
| 수영 `sorrel` | Ceccanti et al. 2021, Biol Trace Elem Res 199:3553 (doi:10.1007/s12011-020-02467-3, PMID 33150483, PMC8257512) | `rumex_acetosa_oxalate_2021`, `ceccanti_…`, `di_noia_…`, `di_gioia_…` | **전문 확인**: PMC 전문 Table 5에 노지 재배 잎 옥살산 8.50 ± 0.21 mg/g FW | 네 기록이 같은 결과를 반복한다. `rumex_acetosa_oxalate_2021`을 대표로 두고 나머지 3건은 `same_finding_as`로 연결했다(삭제 아님). `ceccanti_…`에 DOI·PMID를 추가했다. |
| 수영 (참고) | 같은 논문 | — | — | 기록 ID의 `di_noia`·`di_gioia`는 이 논문의 저자명이 아니다(저자: Ceccanti, Brizzi, Landi, Incrocci, Pardossi, Guidi). 판정이 ID를 참조하므로 ID는 바꾸지 않았다. |
| 버드나무잎 `willowleaf` | Piątczak et al. 2020, Biomolecules 10:1391 (doi:10.3390/biom10101391) | `piatczak_salix_alba_leaf_2020`, `…_phenolics_2020` | **초록 확인** | 서로 다른 결과다. 한 기록은 잎 페놀 화합물 29종을 동정했고, 다른 기록은 총페놀 5575.96 mg/100 g DW를 정량했다. 카드는 둘 다 두고 출처는 1곳으로 센다. |
| 보리지 `borage` | Sattler et al. 2023, Talanta 258:124425 | `sattler_borago_pa_2023`, `sattler_borage_pa_2023` | **초록 확인** | 뒤 기록의 내용이 앞 기록에 포함된다. 하나로 합쳐 표시한다. |
| 보리지 `borage` | Sattler et al. 2025, Food Control (doi:10.1016/j.foodcont.2024.110930) | `sattler_borago_pa_2025`, `sattler_borage_pa_2025` | **원문 미확인**: 초록·전문을 확보하지 못함 | 내용이 겹쳐 보이지만 원문으로 확인하지 못했다. 그래서 합치지 않고 카드를 둘 다 둔다. 출처는 1곳으로 세고 수동 검토 목록에 올렸다. |
| 왕포아풀 `meadowgrass` | Kew POWO 417792-1 | `kew_poa_pratensis_identity`, `…_animal_food` | 두 기록의 문장이 완전히 같음. POWO 페이지는 다시 열람하지 못함 | 하나로 합쳐 표시한다. |

여러 판정이 같은 원문을 공유하는 경우는 원문 단위 ID(`source_id`)로 묶이도록 했다. 이 경우 한 판정 안에서는 중복이 아니다. 예: Tortoise Trust 식물 목록 4건, The Tortoise Table 622·627·94·736·313번 페이지.

## 3. 작업 2 — `tt_melon_624`와 `tt_watermelon_624`

The Tortoise Table 624번 페이지를 다시 받아 읽었다(SHA-256 `7c94d18b…`).

- 제목: "Melon (Cantaloupe, Muskmelon, **Watermelon**, Ogen Melon, Honeydew, Galia)"
- 학명: "Citrullus lanatis spp., Cucumis melo spp." (lanatis는 원문 표기)
- 분류: Feed Sparingly
- 본문: "The leaves and flowers of melons can be nibbled, but should be fed sparingly."

판단은 다음과 같다.

- 수박은 이 페이지 학명·일반명에 직접 들어 있다. 따라서 수박잎 기록은 멜론 자료를 수박에 옮겨 쓴 것이 아니다.
- 그렇다고 독립된 수박잎 근거도 아니다. 두 식물을 한 항목으로 묶은 페이지의 같은 문장 하나다.

처리는 다음과 같다.

- 두 기록의 제목·식물 범위·요약에 "멜론과 수박을 한 항목으로 묶은 페이지의 같은 문장"임을 밝혔다. 두 기록은 같은 원문(`thetortoisetable:plant=624`)으로 묶인다.
- 멜론잎·수박잎 판정 한계에 "수박잎(멜론잎)만 따로 다룬 독립 자료는 없음"을 추가했다.
- 판정(C, 소량 보조)은 원문 분류(Feed Sparingly)와 일치해 유지했다.
- 확실성 C+는 단일 항목 근거치고 높으므로 C로 낮추는 안을 7절에 제안했다(미적용).

## 4. 작업 3 — 검색·목록 페이지를 가리키던 13건

식물별 주소는 추측해서 만들지 않았다. 사이트의 A–Z 목록 26쪽을 내려받아 사이트가 게시한 링크에서 가져왔고, 각 페이지를 1.5초 간격으로 받아 읽었다. 13건 모두 페이지 분류가 기존 기록의 분류와 일치했다.

| 식물 | 기록 | 이전 주소 | 새 주소 | 페이지 이름 / 학명 | 페이지 분류 |
|---|---|---|---|---|---|
| 사과나무잎 | `tortoise_table_apple_tree` | 검색(빈 검색어) | `?plant=23` | Apple (Tree) / Malus domestica | Feed Sparingly |
| 자작나무잎 | `tortoise_table_birch` | 검색 "oak tree varieties" | `?plant=643` | Birch / Betula spp. | Feed in Moderation |
| 수레국화 | `tortoise_table_cornflower` | 꽃 색 목록 | `?plant=104` | Cornflower (Wild) / Centaurea cyanus | Feed in Moderation |
| 코스모스 | `tortoise_table_cosmos` | 꽃 색 목록 | `?plant=491` | Cosmos / Cosmos spp. | Feed in Moderation |
| 에키네시아 | `tortoise_table_echinacea` | A–Z C | `?plant=101` | Coneflower (Echinacea) / Echinacea | Safe to Feed |
| 은행잎 | `tortoise_table_ginkgo` | 검색 "- name" | `?plant=650` | Ginkgo / Ginkgo biloba | Feed Sparingly |
| 민들레아재비류 | `tortoise_table_hawkbit` | A–Z H | `?plant=127` | Hawkbit / Leontodon spp. | Safe to Feed |
| 조밥나물류 | `tortoise_table_hawkweed` | A–Z H | `?plant=640` | Hawkweed (Hieracium) / Hieracium spp. | Feed in Moderation |
| 하와이무궁화 | `tortoise_table_hibiscus_rosa` | A–Z H | `?plant=711` | Hibiscus (China Rose …) / Hibiscus rosa-sinensis | Safe to Feed |
| 라벤더 | `tortoise_table_lavender` | 검색 "enclosure" | `?plant=218` | Lavender / Lavandula spp. | Feed in Moderation |
| 복숭아나무잎 | `tortoise_table_peach_tree` | 검색 "apple tree with apples" | `?plant=615` | Peach Tree / Prunus persica | Feed Sparingly |
| 배나무잎 | `tortoise_table_pear_tree` | 검색 "apple tree with apples" | `?plant=606` | Pear Tree / Pyrus spp. | Feed Sparingly |
| 아욱잎 | `tt_malva_spp_safe` | 검색 "Mallow" | `?plant=363` | Mallow / Malva spp. | Safe to Feed |

`data/tortoise_table_link_audit_20261010.json`의 13개 항목은 다음과 같이 바꿨다.

- 페이지 이름·학명·분류와 확인일(2026-10-15)을 채웠다.
- 이전 주소는 `previous_url`에 남겼다.

같은 목록 주소를 공유하던 탓에 서로 다른 식물이 한 출처처럼 묶였던 경우도 모두 풀렸다. 수레국화·코스모스, 민들레아재비류·조밥나물류·하와이무궁화, 배나무·복숭아나무가 그런 경우였다.

## 5. 작업 4 — 한국 아욱 (Malva verticillata)

판정은 아욱잎 `mallowleaf`, 육지거북 일반, 혼합식 가능(A), 확실성 C다.

연결 근거는 `tt_malva_spp_safe` 1건이다.

- 기록이 가리키던 주소는 검색 페이지였다. 지금은 The Tortoise Table Mallow 항목(363번)이다.
- 이 항목은 Malva spp. 전체를 Safe to Feed로 분류하고, "All tortoises enjoy a snack on mallow flowers and leaves"라고 쓴다.
- Malva verticillata라는 이름은 나오지 않는다.
- 기존 요약에는 "지중해 육지거북 적합 식물 목록에 포함"이라는 문장이 있었다. 이 내용은 Mallow 항목에 없어서 삭제하고, 항목이 실제로 말하는 내용만 남겼다.

Malva verticillata에 대한 종별 직접 근거는 찾지 못했다. 연결된 근거에도, 이번에 확인한 자료에도 이 종을 육지거북에게 먹인 기록이나 시험은 없다.

- 같은 페이지는 아욱 `mallow`(Malva spp., C / C-)와 말바 `commonmallow`의 근거이기도 하다. 세 판정의 근거는 모두 속 수준이다.
- Musk Mallow(6번, Malva moschata) 항목도 있다. 이 항목은 질소가 많은 흙에서 자란 잎에 질산염이 쌓일 수 있다고 쓴다. 다른 종에 대한 내용이라 아욱잎 근거로 연결하지 않았다.

판정은 유지했다.

- 위험 근거가 없으므로, 근거가 부족하다는 이유만으로 등급을 낮추지 않았다.
- 대신 판정 설명과 적용 범위를 다시 썼다. "근거는 Malva속 전체를 다룬 전문 자료 1곳뿐이고, 한국 아욱 자체를 먹인 기록·시험은 확인되지 않았으며, 그 자료도 이 종을 따로 언급하지 않는다."
- 같은 사실을 영어 화면에도 같은 의미로 번역했다.
- 자동 QA의 "종 수준 급여 근거 없음" 수동 검토 목록에 올렸다.

## 6. 그 밖에 바로잡은 것

- `costan_rumex_defences_2023`(소리쟁이): DOI가 같은 호의 반딧불이 페로몬 논문(PMID 36920582)을 가리켰다. 제목·PMID 37121960에 맞는 DOI 10.1007/s10886-023-01427-0으로 고쳤다.
- `bhandari_cauliflower_glucosinolates_2015`(콜리플라워잎): DOI가 같은 호의 p38α MAPK 논문(PMID 26334265)을 가리켰다. 제목·PMID 26334264에 맞는 DOI 10.3390/molecules200915827로 고쳤다.
- PMID 추가: PubMed에서 DOI 하나에 같은 제목의 PMID 하나로 대응되는 것만 넣었다. 대상은 `tgraeca_alfalfa_context_2019`, `marotti_tagetes_thiophenes_2010`, `actinidia_deliciosa_leaf_genotoxicity_2026`, `actinidia_leaf_calcium_oxalate_1987`, `padilla_turnip_leaf_glucosinolates_2007`, 그리고 수영 기록 3건이다.
- `tortoise_table_strawberry`(딸기잎): 기록은 재배 딸기(Fragaria × ananassa)를 대상 종으로 적었다. 그런데 Strawberry 항목(293번)은 Fragaria spp. 속 항목이고 재배종을 따로 언급하지 않는다. 식물 범위를 원문대로 고쳤다.

## 7. 제안 (적용하지 않음, 승인 필요)

- 아욱잎: 확실성을 C에서 C-로 낮추거나, 아욱잎(A/C)과 아욱(C/C-)을 한 번에 결정한다. PR #287에도 같은 항목이 있다.
- 멜론잎·수박잎: 확실성을 C+에서 C로 낮춘다. 근거가 항목 하나, 문장 하나이고 두 판정이 공유한다.
- 사과나무잎: 판정 한계에 원문의 주의를 추가한다. Apple (Tree) 항목은 오래되어 시드는 잎에서 시안 화합물이 생기니 떨어진 잎을 먹지 않게 하라고 쓴다. 복숭아나무잎 판정에는 이미 이 주의가 있다.

## 8. 자동 QA (`scripts/qa_public_evidence_integrity_v1.py`)

CI에서는 `plant-data-integrity-qa.yml`이 이 검사를 실행한다. 결정 기록을 다시 적용했을 때 데이터에 차이가 생기지 않는지도 확인한다.

| 검사 | 수정 후 결과 | 수정 전 데이터(main)에 적용한 결과 |
|---|---|---|
| 1. 존재하지 않는 evidence_id 참조 | 통과 | 통과 |
| 2. 판정 식물이 근거 기록의 대상 식물에 없음 | 통과 | 통과 |
| 3. 식별자: `source_id` 누락·불일치, DOI·PMID 필드와 URL 불일치, 같은 DOI·PMID·PMCID·페이지에 여러 `source_id` | 통과 | 실패 (`source_id` 없음 277건, PMC8257512가 두 원문으로 갈림) |
| 4. `same_finding_as` 연결 오류 | 통과 | 통과 |
| 5. 한 판정이 같은 원문을 설명 없이 중복 인용 | 통과 | 실패 3건 (수영·보리지 2023·왕포아풀) |
| 6. 검색·목록 페이지를 근거로 사용 | 통과 | 실패 13건 |
| 7. 전문 DB 항목이 판정 식물의 속을 다루지 않음 | 통과 | 통과 |
| 8. 원문이 다루지 않는 종을 기록이 주장 | 통과 | 실패 1건 (딸기) |

검사가 실제로 실패를 잡는지도 확인했다. 데이터를 일부러 바꾼 상태에서 다음 네 가지 모두 실패로 나왔다.

- 같은 DOI에 다른 `source_id`를 붙인 경우
- 같은 결과 연결(`same_finding_as`)을 지운 경우
- 수박잎 기록을 Mallow 페이지로 바꾼 경우
- 원문에 없는 종을 기록에 적은 경우

자동으로 판단할 수 없는 학술 문제는 통과나 실패로 처리하지 않았다. 아래 수동 검토 목록으로 따로 모았다. 목록에 올랐다고 해서 판정이 틀렸다는 뜻은 아니다.

| 분류 | 건수 | 예 |
|---|---|---|
| 종 수준의 급여 근거 없이 속 또는 더 넓은 범위 자료만 있는 판정 | 29 | 아욱잎, 제비꽃잎·꽃(Viola mandshurica), 포도잎, 라벤더, 코스모스, 에키네시아, 배나무잎, 딸기잎 |
| 여러 식물에 걸친 사육지침인데 식물별 범위가 적히지 않은 기록 | 14 | BCG·Tortoise Trust·Merck 지침 |
| 한 항목이 여러 분류군을 함께 다룸 | 4 | Melon(멜론·수박), Cat Grass, Mulberry(뽕나무·꾸지나무), Bean Sprouts(녹두·대두) |
| 기록이 원문에 없는 종을 선언하고 적용 (국내 기준 식물 등) | 6 | 쑥(Artemisia princeps), 들깨, 파프리카, 미나리(Oenanthe javanica), 딸기 |
| 같은 원문의 여러 기록, 관계 확인 필요 | 2 | 버드나무 2020(초록 확인), 보리지 2025(원문 미확인) |
| DOI·PMID가 없는 논문 기록 | 4 | |
| 어떤 판정도 인용하지 않는 기록 | 3 | |

Tortoise Table 항목이 다루는 학명은 `data/tortoise_table_page_taxa_v1.json`에 저장했다. 공개 근거가 쓰는 127개 항목을 받아 페이지 학명, 본문에 적힌 학명, 분류, SHA-256만 남겼고 본문은 저장하지 않았다. QA는 이 파일을 오프라인으로 읽는다. 다시 확인하려면 `python scripts/build_tortoise_table_page_taxa_v1.py --live`를 실행한다.

## 9. 아직 검증하지 못한 것

- Sattler et al. 2025(Food Control): 초록·전문 모두 확보하지 못했다. 두 기록의 관계를 확인하지 못했다.
- Kew POWO Poa pratensis 페이지: 이번에 다시 열람하지 못했다(API가 JSON을 주지 않음). 중복 판단은 두 기록의 문장이 같다는 점에만 근거한다.
- 버드나무 2020, 보리지 2023: 초록만 읽었고 전문은 읽지 않았다.
- DOI 정정 2건과 PMID 추가: PubMed 서지 기록으로 확인했고 논문 본문은 읽지 않았다. 각 기록 요약의 내용 검증은 이번 범위가 아니다.
- 수동 검토 목록 62건: 사람이 원문을 읽고 판단해야 한다. 특히 종 수준 근거가 없는 판정 29건이 있다.
