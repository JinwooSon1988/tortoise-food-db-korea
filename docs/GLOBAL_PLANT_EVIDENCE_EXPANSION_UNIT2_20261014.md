# 전 세계 육지거북 먹이 식물 근거 확장: 2차 단위 (2026-10-14)

1차 단위(PR #304, `docs/GLOBAL_PLANT_EVIDENCE_EXPANSION_20261014.md`) 위에 쌓은 추가분이다. 1차 파일(`*_v1.json`)은 고치지 않았고 새 파일만 더했다. 공개 사이트 데이터, 급여 판정, 페이지 생성기, UI, 번역, CI 설정은 바꾸지 않았다. 여기 실린 기록에는 급여 등급이 없다.

## 1. 추가한 파일

| 파일 | 내용 |
|---|---|
| `data/research/global_plant_evidence_transcription_v2.json` | 2차에 읽은 출처 14건의 전사본, 1차 기록의 1차 문헌 대조 결과, 영양 표 전사. 나머지 파일의 원천 |
| `data/research/forage_table_selection_v2.json` | 2차 후보 식물용 Feedipedia 성분표 선택 목록 |
| `data/research/global_evidence_sources_v2.json` | 출처 14건, 1차 기록이 인용한 문헌 23묶음의 확보 상태, 보류 목록 |
| `data/research/tortoise_species_registry_v2.json` | 추가한 육지거북 2분류군 |
| `data/research/tortoise_plant_evidence_v2.json` | 추가 근거 357건 |
| `data/research/primary_verification_ledger_v2.json` | 1차 근거 169건 각각에 대해, 인용된 1차 문헌을 읽었는지와 그 결과 |
| `data/research/plant_candidates_v2.json` | 1·2차 누적 식물 이름 483개의 학명 대조와 기존 DB 연결 |
| `data/research/forage_nutrition_research_v2.json` | 추가 영양 기록 46건(수치 248개) |
| `data/research/research_layer_summary_v2.json` | 1차, 2차 추가분, 누적 집계 |
| `scripts/build_global_plant_evidence_research_v2.py` | 전사본 v2를 위 파일들로 펼침 |
| `scripts/qa_global_plant_evidence_research_v2.py` | 오프라인 검증 |

## 2. 1차 대비 증가량

| 항목 | 1차 | 2차 추가 | 누적 |
|---|---|---|---|
| 식물 기록이 있는 출처 | 16 | 14 | 30 |
| 종별 섭식·급여 근거 | 169 | 357 | 526 |
| 그중 1차 연구를 직접 읽은 근거 | 46 | 323 | 369 |
| 근거가 연결된 육지거북 분류군 | 15 | 4 | 19 |
| 식물 이름 | 199 | 284 | 483 |
| 기존 DB에 없는 신규 후보 | 129 | 218 | 347 (종 293, 속 54) |
| 영양 기록 | 11 (수치 113) | 46 (수치 248) | 57 (수치 361) |
| 씨앗 혼합물 | 6 | 0 | 6 |

2차에 추가한 근거의 출처 언어는 영어 10건, 스페인어 2건, 프랑스어 1건, 폴란드어 1건이다. 독일어와 이탈리아어 자료는 넣지 못했다.

## 3. 근거의 깊이: 1차 기록 대조 결과

1차 단위에서 종 계정이 다른 문헌을 인용해 적은 102건이 대상이다.

| 결과 | 건수 |
|---|---|
| 인용된 1차 문헌을 읽어 확인 | 20 (그대로 확인 16, 차이가 있어 차이를 적음 4) |
| 인용된 문헌 중 읽은 것에는 그 식물이 없음. 함께 인용된 다른 문헌은 미열람 | 5 |
| 1차 문헌을 읽지 못해 2차 인용으로 유지 | 77 |

이와 별도로, 1차 단위에서 사육자 사이트 전재본만 읽어 보류했던 러시아육지거북 4건은 논문 전문(Lagarde 외 2003)을 읽어 확인했다(그중 1건은 원문이 종명까지 적어 차이를 기록).

읽은 1차 문헌과 확인한 기록:

- Moll·Klemens 1996(팬케이크육지거북, 탄자니아): 5건. 계정이 속명만 적은 *Achyranthes*는 원문에 *Achyranthes aspera* 잎으로 적혀 있다. *Panicum* sp.는 배설물이 아니라 섭식 관찰이다.
- Platt 외 2001(버마별거북, 미얀마): 5건. 원문은 사냥꾼의 말이며 버마별거북과 노란머리육지거북을 함께 가리킨다.
- Sriprateep 외 2013(노란머리육지거북, 태국): 8건 확인. 계정이 같은 문장에 인용한 *Chromolaena odorata* 등 5건은 이 논문에 없다.
- Bayley·Highfield 1996(그리스육지거북, 모로코): 1건. 원문에는 'Opuntia spp.'로만 적혀 있고 계정의 *Opuntia maxima*라는 종명은 없다.
- Lambert 1993(설카타, 말리): 1건. 사육되던 암컷 한 마리를 풀어 두었을 때의 관찰 한 번이다.

인용 문헌 23묶음의 확보 상태는 `global_evidence_sources_v2.json`의 `cited_primary_status`에 있다. 읽은 것 4, 일부만 읽은 것 1, 검색했으나 공개 전문을 찾지 못한 것 2, 위치는 찾았으나 내려받지 못한 것 1, 1차 단위에서 403으로 막힌 것 1, 이번 단위에서 찾아보지 않은 것 14다.

'독립된 1차 기록'은 인용 문헌의 확인과 구분했다. 같은 거북과 같은 식물을 다른 1차 연구가 따로 기록한 경우로, 1차 기록 9건에 해당한다. 장부의 `independent_primary_records_same_tortoise_and_plant`에 적었고 확인 건수에는 넣지 않았다.

## 4. 종별 자료 확보 현황(누적)

| 육지거북 | 1차 | 2차 추가 | 누적 | 1차 연구 직접 열람 |
|---|---|---|---|---|
| 산티아고 코끼리거북 *Chelonoidis darwini* (갈라파고스) | 0 | 90 | 90 | 90 |
| 고퍼육지거북 *Gopherus polyphemus* | 0 | 62 | 62 | 62 |
| 알다브라 코끼리거북 *Aldabrachelys gigantea* | 0 | 53 | 53 | 53 |
| 노란머리육지거북 *Indotestudo elongata* | 14 | 28 | 42 | 22 |
| 모하비사막거북 *Gopherus agassizii* | 24 | 16 | 40 | 34 |
| 그리스육지거북 서부 아종군 *Testudo graeca* | 12 | 24 | 36 | 24 |
| 러시아육지거북 *Testudo horsfieldii* | 4 | 28 | 32 | 28 |
| 헤르만육지거북 *Testudo hermanni* | 13 | 16 | 29 | 0 |
| 표범육지거북 *Stigmochelys pardalis* | 28 | 0 | 28 | 28 |
| 붉은발육지거북 *Chelonoidis carbonarius* | 1 | 24 | 25 | 19 |
| 마지네이티드육지거북 *Testudo marginata* | 18 | 0 | 18 | 0 |
| 버마별거북 *Geochelone platynota* | 10 | 6 | 16 | 0 |
| 팬케이크육지거북 *Malacochersus tornieri* | 6 | 7 | 13 | 6 |
| 설카타 *Centrochelys sulcata* | 11 | 1 | 12 | 1 |
| 스피크경첩거북 *Kinixys spekii* | 11 | 0 | 11 | 0 |
| 트라방코르육지거북 *Indotestudo travancorica* | 9 | 0 | 9 | 0 |
| 인도별거북 *Geochelone elegans* | 6 | 0 | 6 | 0 |
| 아시아숲거북 *Manouria emys* | 2 | 0 | 2 | 0 |
| 갈라파고스 코끼리거북류(산타크루스섬 2종) | 0 | 2 | 2 | 2 |

우선 조사 대상 가운데 노란발육지거북은 이번에도 식물 이름이 있는 근거를 넣지 못했다. 설카타는 말리의 관찰 1건만 늘었다.

읽을 때 주의할 점:

- 알다브라 코끼리거북 53건은 원서식지가 아니라 모리셔스 라운드섬에 도입되어 방사된 개체군의 자료다(Moorhouse-Gann 외 2022).
- 산티아고 코끼리거북 90건(Pillajo 2020, 스페인어 학위논문)과 고퍼육지거북 62건(Figueroa 외 2024)은 배설물 속 씨앗으로 식물을 동정했다. 씨앗 없이 먹은 잎은 잡히지 않는다. 학위논문은 동료 심사 논문이 아니어서 상태를 따로 두었다(`verified_primary_source_thesis`).
- 붉은발육지거북 24건 가운데 야생 기록은 5건이고, 그 5건은 논문 서론이 다른 연구(Moskovits 1981)를 옮긴 것이라 1차 문헌 미열람이다. 나머지 19건은 콜롬비아의 사육 시험과 그 농장의 평소 급여다.
- 헤르만육지거북 16건은 프랑스 국가행동계획의 요약 문단이며 과 이름이나 프랑스어 일반명 수준이다.

## 5. 근거의 종류 구분(2차 추가 357건)

| 종류 | 건수 |
|---|---|
| 야생 섭식 연구 | 262 |
| 사육 급여 시험 | 28 |
| 자연 식생 울타리 안 섭식 연구(사막거북 유체) | 16 |
| 보전계획 문헌 요약 | 16 |
| 주민이 야생 개체에게 준 먹이(태국 마을) | 14 |
| 현지 사냥꾼 보고 | 12 |
| 사육 급여 관행 | 9 |

영양성분 분석은 근거 파일이 아니라 영양 파일에 따로 두었다. 독성 연구는 이번 단위에 넣은 것이 없다. 원문이 독성을 함께 적은 경우는 그 기록의 한계 문장에 남겼다. 예: Lagarde 외 2003은 러시아육지거북이 먹은 *Papaver pavoninum*, *Koelpinia linearis*, *Ceratocephalus*가 포유류에 독성이 있는 식물이라고 적었다.

회피·거부 기록은 6건이다(러시아육지거북의 벼과 풀과 *Alyssum desertorum*, 헤르만육지거북의 타임·로즈메리·침엽수·대극류).

## 6. 학명 대조

2차에 새로 나온 식물 이름 327개를 GBIF와 대조했다.

| 결과 | 개수 |
|---|---|
| 수용명 | 251 |
| 이명(원문 표기 유지, 수용명 병기) | 30 |
| 속명 원문 유지 | 1 |
| 철자가 달라 검토 필요 | 13 |
| 동명이명이 여럿이고 원문에 명명자가 없어 확정 불가 | 7 |
| 대조되지 않음 | 4 |
| GBIF 결과가 원문 서술과 충돌해 채택하지 않음 | 1 |
| 같은 출처가 이명과 수용명을 서로 다른 식물로 적어 합치지 않음 | 1 |
| 일반명만 있음 | 19 |

- 동명이명 7건은 GBIF가 돌려준 후보들을 `backbone_homonyms`에 그대로 남겼다. 예: 'Prunus dulcis'는 명명자에 따라 *Prunus avium* 또는 *Prunus amygdalus*의 이명이다.
- *Ceratocephalus falcatus*는 GBIF가 국화과 *Achillea falcata*의 이명으로 돌려주지만, 논문은 미나리아재비속과 가깝고 라눙쿨린을 가진 식물로 적었다. 채택하지 않고 검토 대상으로 두었다.
- Figueroa 외 2024는 *Euphorbia cyathophora*와 *Euphorbia heterophylla*를 따로 적었다. GBIF는 앞의 것을 뒤의 것의 이명으로 보지만 합치지 않았다.
- 출처가 적은 과 이름이 GBIF의 과와 다른 8건은 `family_differs_from_backbone`으로 표시만 했다(과 범위가 바뀐 경우들).

## 7. 영양자료

| 구분 | 기록 | 내용 |
|---|---|---|
| Oftedal 외 2002, 표 6 | 15 | 사막거북 유체가 실제로 먹은 부위(잎, 어린 줄기, 미숙과 등)의 수분(생체중 기준), 조단백질·칼륨(건물 기준) |
| Długosz 외 2015, 표 2 | 18 | 급여 시험에 쓴 풀 6종, 과일 6종, 채소 6종의 건물, 조섬유, 조회분, 조단백질, 조지방 |
| Feedipedia | 13 | 후보 식물과 같은 종의 표 12건(생초 9, 건초 1, 건조 1, 짚 1), 같은 속 다른 종 참고용 1건(건초) |

상태별로는 생초·생과 42, 건초 2, 건조 1, 짚 1이다.

- Oftedal의 칼륨배설잠재지수(PEP)는 계산값이라 넣지 않았다. 같은 논문의 표 5(만난 식물 전체의 성분)는 전사하지 않았다.
- Długosz의 표는 모든 열을 '%'로만 적고 기준을 밝히지 않았다. 각 행의 성분 합이 건물 함량보다 작아 생체중 기준으로 보이지만 논문이 그렇게 적지는 않았으므로 기준을 '표에 명시 없음'으로 두었다. 이 논문은 자두(śliwka)에 아몬드의 학명 *Prunus dulcis*를 적어 그 항목은 동정이 불확실하다.
- *Stenotaphrum secundatum* 건초 표는 근거에 나온 *Stenotaphrum dimidiatum*과 종이 다르다. 참고용으로만 두고 후보 식물에 연결하지 않았다.
- *Tithonia diversifolia* 표는 잎과 줄기 자료이고, 거북 근거는 꽃이다. 부위가 다르다는 점을 기록에 적었다.
- 영양 기록은 모두 `feeding_verdict_use: false`다. 성분이 있다는 사실은 급여 안전성의 근거가 아니다.

## 8. 보류와 남은 공백

- 출처 보류 12건: Milton 1992(학술지 페이지가 빈 응답), Gibson·Hamilton 1983(알다브라, 비공개), Del Vecchio 외 2011(헤르만, 403), Blake 외 2015, Moskovits·Bjorndal 1990, Soler 외 2012, Richard 1994(차코육지거북), Rodrigues·Galetti(포르투갈어, 403), Strong·Fragoso 2006, Jerozolimski 외 2009(노란발, 404), Sánchez 학위논문(식이 내용 없음), Nature Seychelles 기사.
- 씨앗 혼합물 보류 3건: 프랑스 Truffaut(403), 독일 Kiepenkerl(판매 페이지에 구성 식물 목록 없음), 이탈리아 Testumix(공급처 페이지 못 찾음). 이번 단위에서 새로 넣은 혼합물은 없다.
- 1차 단위에서 넘어온 보류 4건을 풀었다: Oftedal 2002, PMC11573422, PMC6386306(식물 이름 없음), Lagarde 2003.
- 남은 공백: 노란발육지거북, 원서식지 알다브라 자료, 설카타 야생 식이, 독일어·이탈리아어 원문, 영국 밖 씨앗 혼합물, 1차 문헌을 읽지 못한 77건.
- Moorhouse-Gann 2022의 표 3은 PDF 글자층에서 스크립트로 옮겼다. DNA와 관찰 열은 표에 인쇄된 합계(47, 24)와 맞지만 배설물 형태 열은 23으로 인쇄 합계 21과 다르다. 원인을 찾지 못해 출처 기록에 적어 두었다.

## 9. 재현과 검증

```
python scripts/build_global_plant_evidence_research_v2.py --cache <GBIF 응답 캐시 폴더> --feedipedia-cache <Feedipedia 페이지 캐시 폴더>
python scripts/qa_global_plant_evidence_research_v2.py
```

검증 스크립트는 네트워크 없이 돈다. 중복(ID, 출처 URL, 같은 출처 안의 같은 기록), 학명(대조를 통과하지 않은 이름에 수용명 금지, 조회명은 원문 표기의 표기상 변형만 허용), 출처(전문 열람 여부와 상태), 부위와 상태, 단위와 기준, 근거 직접성(다른 문헌을 인용한 기록이나 읽지 않은 문헌을 직접 검증으로 표시하면 실패), 전사본과의 일치, 급여 등급 부재, 1차 후보와 연결의 보존, 집계 재계산을 확인한다. CI 워크플로에는 연결하지 않았다.
