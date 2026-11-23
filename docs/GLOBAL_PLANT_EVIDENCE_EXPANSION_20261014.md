# 전 세계 육지거북 먹이 식물 근거 확장: 1차 단위 (2026-10-14)

이 문서는 연구용 데이터 계층 `data/research/`의 첫 구축분을 설명한다. 공개 사이트 데이터, 급여 판정, 페이지 생성기, UI, CI 설정은 바꾸지 않았다. 여기 실린 기록에는 급여 등급이 없다.

## 1. 무엇을 만들었나

| 파일 | 내용 |
|---|---|
| `data/research/global_plant_evidence_transcription_v1.json` | 원문에서 읽은 식물명과 섭식 서술을 원문 표기 그대로 옮긴 전사본. 나머지 파일의 원천 |
| `data/research/forage_table_selection_v1.json` | 후보 식물과 종이 같은 Feedipedia 성분표 선택 목록 |
| `data/research/global_evidence_sources_v1.json` | 출처 19건, 저장소에 이미 있는 출처 2건, 보류 출처 9건 |
| `data/research/tortoise_species_registry_v1.json` | 육지거북 19분류군의 학명 대조 결과 |
| `data/research/tortoise_plant_evidence_v1.json` | 종별 섭식·급여 근거 169건 |
| `data/research/enclosure_seed_mixtures_v1.json` | 야외 방사장 씨앗 혼합물 6건, 보류 4건 |
| `data/research/plant_candidates_v1.json` | 근거와 혼합물에 나온 식물 이름 199개의 학명 대조와 기존 DB 연결 |
| `data/research/forage_nutrition_research_v1.json` | 생초·건초·건조 사료 성분 기록 11건(수치 113개) |
| `scripts/build_global_plant_evidence_research_v1.py` | 전사본을 위 파일들로 펼치고 GBIF로 학명을 대조 |
| `scripts/qa_global_plant_evidence_research_v1.py` | 오프라인 검증 |

## 2. 실제 확인된 수치

| 항목 | 수치 |
|---|---|
| 기존 등록 식물 | 182건(고유 181종) |
| 근거·혼합물에 나온 식물 이름 | 199개 |
| 그중 기존 DB에 없는 신규 후보 | 129개(종 수준 95, 속 수준 34) |
| 기존 DB에 같은 종이 있음 | 17개 |
| 기존 DB에 속 수준 기록만 있음 | 25개 |
| 후보에서 제외 | 28개: 이름 미확정 15, 일반명만 있음 7, 과 수준 6 |
| 학명 대조 통과(식물) | 176개: 수용명 152, 이명 21, 속명 원문 유지 3 |
| 학명 대조 통과(육지거북) | 19분류군 전부 |
| 종별 섭식·급여 근거 | 169건 |
| 근거가 연결된 육지거북 분류군 | 15개 |
| 씨앗 혼합물 | 6건, 구성 항목 80개 |
| 혼합물 구성 식물(학명 확인) | 32종. 일반명만 있는 항목 28개는 미확정 |
| 신규 영양 기록 | 11건: 생초 6, 건초 2, 건조 2, 짚 1 |
| 출처 | 19건: 전문 열람 15, 초록만 3, 2차 전재만 1 |
| 중복 제거 | 출처 2건(저장소에 이미 있음), 혼합물 구성 중복 표기 1건 |
| 검증 보류 | 출처 9건, 혼합물 4건, 근거 기록 4건 |

출처 언어는 19건 모두 영어다. 조사 지역은 남아프리카 3, 미국 2, 그 밖에 사헬, 미얀마, 인도, 인도·파키스탄·스리랑카, 그리스·알바니아·이탈리아, 지중해 유럽, 모로코·알제리·튀니지·스페인, 남·동남아시아, 짐바브웨, 탄자니아·케냐, 태국, 브라질, 우즈베키스탄, 알제리가 각 1건이다.

## 3. 종별 근거 건수

| 육지거북 | 근거 | 주된 출처 |
|---|---|---|
| 표범육지거북 *Stigmochelys pardalis* | 28 | Mason 외 1999, 남아프리카 Valley Bushveld. 식이 비율 표를 직접 판독 |
| 모하비사막거북 *Gopherus agassizii* | 24 | Jennings 2002(섭식 횟수 비율 표), 종 계정 2019 |
| 마지네이티드육지거북 *Testudo marginata* | 18 | 종 계정 2023 |
| 노란머리육지거북 *Indotestudo elongata* | 14 | 종 계정 2016 |
| 헤르만육지거북 *Testudo hermanni* | 13 | 종 계정 2011 |
| 그리스육지거북 서부 아종군 *Testudo graeca* | 12 | 종 계정 2022 |
| 설카타 *Centrochelys sulcata* | 11 | 종 계정 2020 |
| 스피크경첩거북 *Kinixys spekii* | 11 | 종 계정 2021 |
| 버마별거북 *Geochelone platynota* | 10 | 종 계정 2011 |
| 트라방코르육지거북 *Indotestudo travancorica* | 9 | 종 계정 2011 |
| 인도별거북 *Geochelone elegans* | 6 | 종 계정 2018. 과 수준 기록뿐 |
| 팬케이크육지거북 *Malacochersus tornieri* | 6 | 종 계정 2018 |
| 러시아육지거북 *Testudo horsfieldii* | 4 | Lagarde 외 2003. 원문 미열람으로 보류 |
| 아시아숲거북 *Manouria emys* | 2 | 종 계정 2015 |
| 붉은발육지거북 *Chelonoidis carbonarius* | 1 | Wang 외 2011. 초록만 |

'종 계정'은 IUCN 거북 전문가그룹이 펴내는 Chelonian Research Monographs 5의 동료 심사 종 계정이다. 계정이 다른 1차 문헌을 인용해 적은 식물은 `evidence_directness`를 `reported_in_account_primary_not_read`로 두었다. 1차 논문을 직접 읽은 기록은 46건이다.

이번 단위에서 근거를 넣지 못한 우선 분류군: 알다브라 코끼리거북, 갈라파고스 코끼리거북류, 노란발육지거북. 알다브라 계정 두 건은 읽었으나 먹이 식물 이름이 없었고, 나머지는 원문을 열지 못했다.

## 4. 읽을 때 지켜야 할 한계

- 야생 섭식 기록은 그 분류군이 그 지역에서 먹었다는 사실만 보여 준다. 사육 급여량, 장기 안전성, 다른 종에 대한 적용은 보여 주지 않는다.
- 원문이 독성을 함께 적은 식물이 있다. 마지네이티드육지거북의 *Drimia maritima*, 헤르만육지거북이 찾아 먹는다고 적힌 *Tamus communis*·*Arum*·*Ranunculus*·*Digitalis*는 원문이 포유류에 독성이 있다고 밝힌 식물이다. 섭식 기록이 있다고 급여 가능하다는 뜻이 아니다.
- 회피·거부 기록 7건(`is_negative_record`)을 함께 보존했다. 예: 헤르만육지거북의 향이 강한 식물, 러시아육지거북의 벼과 풀.
- 씨앗 혼합물은 6건 모두 영국 자료다. 판매처나 동호회가 육지거북용이라고 적었다는 사실은 안전성 근거가 아니다. 구성 식물마다 따로 근거가 필요하다.
- 영양 기록은 가축 사료 성분표다. 반추동물·돼지·가금 소화율과 에너지 값, 계산값(*)은 넣지 않았다. 생초 표와 건초 표는 서로 다른 시료이므로 둘의 차이를 건조에 따른 변화로 읽을 수 없다.
- 학명은 원문 표기를 그대로 두고 GBIF 대조 결과를 옆에 적었다. 철자가 다른 9건(예: 원문의 'Commerlina benghalensis')과 대조되지 않은 7건은 고쳐 쓰지 않고 검토 대상으로 두었다.
- 속명만 적힌 기록은 그 속의 특정 종으로 좁히지 않았다. GBIF가 다른 속의 이명으로 처리하는 속명(Rosmarinus, Galenia)도 원문 범위를 넓히지 않도록 그대로 두었다.

## 5. 보류 목록

- 출처: Oftedal 외 2002(사막 식물 영양 표, 스캔 품질 문제로 수치 미전사), Blake 외 2015(갈라파고스), Gibson·Hamilton 1983(알다브라), Alagar Rajan·Balasubramanian 1991(인도별거북, 403), Moskovits·Bjorndal 1990(붉은발·노란발), PMC 논문 2건(내려받았으나 미열람), 알다브라·경첩거북 계정.
- 혼합물: 프랑스 Truffaut 2건(403), 이탈리아 Testumix(상품 페이지 미확인), 영국 ProRep 다른 판매처(403).
- 근거 기록: Lagarde 외 2003의 4건. 사육자 사이트에 전재된 초록과 발췌만 읽었다.

## 6. 재현 방법

```
python scripts/build_global_plant_evidence_research_v1.py --cache <GBIF 응답 캐시 폴더> --feedipedia-cache <Feedipedia 페이지 캐시 폴더>
python scripts/qa_global_plant_evidence_research_v1.py
```

검증 스크립트는 네트워크 없이 돈다. CI 워크플로에는 연결하지 않았다(이번 작업 범위에서 CI 설정 변경 금지).
