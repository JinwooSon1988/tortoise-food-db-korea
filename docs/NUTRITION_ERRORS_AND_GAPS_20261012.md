# 영양자료 전수 검증: 오류 및 공백 목록 (2026-10-12)

기계 판독용 결과: `data/nutrition_verified_source_check_v1.json`(검증자료 대조 원장), `data/nutrition_coverage_audit_v1.json`(공백 목록).

## 1. 요약

- 검증자료 76건의 수치 843개를 원본 파일과 하나씩 대조했다. 수정 전 1건이 원문과 달랐고, 수정 후 전부 일치한다.
- 참고자료 72건은 직전 작업에서 원문 대조를 마쳤고 이번에 다시 실행해 결과가 같음을 확인했다(자동 대조 50건, 원본 파일에서 스크립트로 생성 14건, 수동 확인 8건).
- 공개 식물 182개 기록 중 검증자료 63, 참고자료만 50, 연결 자료 없음 69. 미나리 중복 1건을 빼면 고유 식물 181종 기준 63 / 49 / 69이다.
- 검증자료로 승격하거나 참고자료로 강등한 기록은 없다. 급여 판정은 바꾸지 않았다.

## 2. 검증자료 원문 대조 결과

| 대조한 원본 | 기록 수 |
|---|---|
| USDA FoodData Central 원본 CSV(SR Legacy 2018-04, Foundation 2026-04-30) | 34 |
| 농촌진흥청 국가표준식품성분표 10.4 식품별 상세 화면 | 21 |
| 농촌진흥청 통합식품영양성분정보 CSV(기준일 2025-12-23) | 8 |
| 학술지 논문 표(PMC 전문 XML), kg당 값을 10으로 나눈 값과 대조 | 5 |
| 일본 식품표준성분표 식품별 화면 | 4 |
| 인도 식품성분표 2017 PDF(행·열 좌표 판독) | 3 |
| 독일 BLS 4.0 원본 워크북 | 1 |

대상은 `plant_nutrition_v56.json`의 식물별 기록 63건과 부위별 기록 3건, `rda_food_composition_v56.json` 10건이다.

## 3. 발견한 오류와 조치

| 위치 | 문제 | 조치 |
|---|---|---|
| `rda_food_composition_v56.json` 비트잎 (F095000B140a) | 저장값이 수분 93.9 g, 식이섬유 2.9 g, 칼슘 79 mg, 인 55 mg이었다. RDA 10.4 원문은 수분 92.9 g, 칼슘 57 mg, 인 54 mg이고 식이섬유 값은 없다. 저장값은 RDA의 어떤 비트 잎 기록과도 맞지 않는다. | 원문 값으로 수정하고 식이섬유를 삭제했다. 이전 값은 `correction` 필드에 남겼다. 이 파일의 값은 공개 화면에 표시되지 않는다. |
| 참고자료 2건(MEXT 06117, JIRCAS)이 숨겨진 중복 ID `waterdropwort`에 연결 | 공개 목록의 미나리 카드가 '자료 없음'으로 분류됐다 | 대표 ID `minari`로 이전 |
| 농촌진흥청 CSV를 쓰는 기록 15건(검증 8, 참고 7)의 출처 링크 | `https://www.data.go.kr/data/15100065/fileData.do`가 '페이지를 찾을 수 없습니다'(404)로 열린다 | 현재 주소 `https://www.data.go.kr/data/15100065/standard.do`(전국통합식품영양성분정보(원재료성식품)표준데이터)로 교체하고 해당 상세 페이지 16개(국문 8, 영문 8)의 링크를 재생성 |
| `verify_nutrition_reference_sources_v1.py` | Feedipedia의 계산값 표시 `*`를 기록의 `equation`과 다른 값으로 보고 17건을 불일치로 표시했다(수치는 일치) | 표기 차이를 같은 뜻으로 처리하도록 수정 |

## 4. 오류는 아니지만 기록해 둘 점

- **USDA JSON과 CSV의 자릿수:** USDA JSON 파일은 값을 유효숫자 3자리 정도로 반올림해 싣는다(예: 근대 수분 92.7). DB는 원본 CSV의 값(92.66)을 저장하고 있어 CSV와는 정확히 일치한다.
- **RDA 판 차이:** 고수는 10.4판(F0170000000a: 수분 91.4 g, 칼슘 79 mg, 인 52 mg)과 2025-12-23 CSV판(R106-017000001-0000: 수분 87.9 g, 칼슘 46 mg, 인 26 mg)의 값이 다르다. DB의 RDA 보조 기록은 10.4판 값이며 그 판과 일치한다. 공개 수치는 USDA 기록을 쓴다.
- **학술지 자료의 단위 환산:** 식용꽃 5건(금어초, 수레국화, 한련화, 팬지, 금잔화)은 논문의 mg/kg·g/kg 생체중 값을 10으로 나눠 100 g 기준으로 저장했다. 환산은 정확하며 기록의 `basis`에 명시돼 있다. 품종 1개, 한 재배지의 값이다.
- **USDA 원문의 학명 오타:** USDA는 근대를 'Beta vulgaris subsp. vulagaris', 로메인을 'Lactuca sativa var. logifolia'로 적는다. 원문 오타이며 DB 학명은 올바르다.

### 속 수준 기록에 종 수준 수치가 연결된 검증자료

마스터 학명이 속 수준(spp.)인데 한 종의 식품 기록을 검증자료로 쓰는 경우다. 국내 표준명 매핑(`data/korea_taxon_mapping_v1.json`)을 근거로 연결돼 있으며, 속 전체의 값으로 읽으면 안 된다.

| 기록 | 마스터 학명 | 원자료 식품 | 매핑된 국내 분류군 | 매핑 상태 |
|---|---|---|---|---|
| 질경이 (`plantain`) | Plantago spp. | 질경이, 생것 (F1700000000a) | Plantago asiatica L. | verified_korea_name |
| 민들레 (`dandelion`) | Taraxacum spp. | 민들레, 생것 (F0780000000a) | Taraxacum platycarpum | verified_korea_name |
| 아욱 (`mallow`) | Malva spp. | 아욱, 생것 (F1230000000a) | Malva verticillata L. | verified_korea_crop |
| 방가지똥 (`sowthistle`) | Sonchus spp. | 방가지똥, 생것 (F0850000000a) | Sonchus oleraceus L. | 상태 미기재 |
| 뽕잎 (`mulberry`) | Morus spp. | 뽕잎, 생것 (F2350000000a) | Morus alba L. | verified_korea_name |
| 비름 (`amaranthleaf`) | Amaranthus spp. | 비름_생것 (R106-093000001-0000) | Amaranthus mangostanus L. | verified_korea_name |

방가지똥은 매핑 상태가 비어 있어 보완이 필요하다.

### 부위 표기가 원문에 없는 검증자료

원자료 식품명에 부위가 따로 적혀 있지 않아 '판매 형태의 잎채소' 또는 '가식부'로 기록한 것이 19건이다: 근대, 로메인, 엔다이브, 물냉이, 케일, 시금치, 루꼴라, 콜라드그린, 청경채, 쑥갓, 콘샐러드, 돌나물, 쑥, 질경이, 민들레, 아욱, 방가지똥, 수영, 비름. 급여 부위(잎)와 일치하는 것으로 보되 원문이 부위를 특정하지 않는다는 점을 기록에 남겨 두었다.

## 5. 직접 측정자료와 참고자료의 구분

| 구분 | 기록 수 | 식물 수 | 저장 위치 |
|---|---|---|---|
| 검증자료(같은 종·부위·생것, 원문 대조 완료) | 63 | 63 | `plant_nutrition_v56.json` |
| 참고자료 | 72 | 52 | `plant_nutrition_reference_v1.json` |
| ↳ dry_matter_reference | 43 | 34 | |
| ↳ related_species_reference | 14 | 11 | |
| ↳ related_part_reference | 11 | 10 | |
| ↳ related_cultivar_reference | 4 | 3 | |

참고자료는 모두 `status: reference_only`, `feeding_verdict_use: false`이며, 새 테스트가 참고자료에 '검증' 표시가 붙는 것을 막는다. 건조물 기준 값은 생체 100 g 기준으로 환산하지 않았다.

## 6. 출처 링크 유효성

영양자료와 근거 레코드의 출처 URL 361개를 요청해 확인했다.

| 결과 | URL 수 |
|---|---|
| 열림 | 288 |
| USDA 단일 페이지 앱(HTTP 404이지만 브라우저에서 열림) | 43 |
| 자동 접근 차단(403), 사람 브라우저로는 미확인 | 16 |
| DOI 등록 확인, 출판사가 자동 접근 차단(403) | 14 |

USDA 식품 상세 주소는 서버가 404 상태 코드와 함께 앱 화면을 보내고 브라우저에서 내용을 그린다. 헤드리스 Chrome으로 1건(FDC 169219)을 열어 식품명이 표시됨을 확인했다.

확인이 필요한 URL:

| 상태 | URL | 쓰인 파일 |
|---|---|---|
| 403 | https://eurekamag.com/research/000/769/000769486.php | public_evidence_records.json |
| 403 | https://healthtopics.vetmed.ucdavis.edu/tags/reptiles | public_evidence_records.json |
| 403 | https://iris.unito.it/retrieve/e27ce42a-913a-2581-e053-d805fe0acbaa/atti_SISVET_2015.pdf | public_evidence_records.json |
| 403 | https://journalejmp.com/index.php/EJMP/article/view/1177 | plant_nutrition_reference_v1.json |
| 403 | https://onlinelibrary.wiley.com/doi/10.1002/leg3.100 | public_evidence_records.json |
| 403 | https://powo.science.kew.org/taxon/1101632-2 | public_evidence_records.json |
| 403 | https://powo.science.kew.org/taxon/417792-1 | public_evidence_records.json |
| 403 | https://powo.science.kew.org/taxon/523575-1 | public_evidence_records.json |
| 403 | https://powo.science.kew.org/taxon/urn%3Alsid%3Aipni.org%3Anames%3A321285-2 | public_evidence_records.json |
| 403 | https://powo.science.kew.org/taxon/urn%3Alsid%3Aipni.org%3Anames%3A523626-1 | public_evidence_records.json |
| 403 | https://powo.science.kew.org/taxon/urn%3Alsid%3Aipni.org%3Anames%3A561932-1 | public_evidence_records.json |
| 403 | https://powo.science.kew.org/taxon/urn:lsid:ipni.org:names:272194-1 | public_evidence_records.json |
| 403 | https://powo.science.kew.org/taxon/urn:lsid:ipni.org:names:289589-1 | public_evidence_records.json |
| 403 | https://powo.science.kew.org/taxon/urn:lsid:ipni.org:names:30036649-2 | public_evidence_records.json |
| 403 | https://powo.science.kew.org/taxon/urn:lsid:ipni.org:names:545734-1 | public_evidence_records.json |
| 403 | https://powo.science.kew.org/taxon/urn:lsid:ipni.org:names:79457-2 | public_evidence_records.json |

## 7. 자료의 발행 연도와 성격

| 자료 | 판·연도 | 성격 | 검증자료 기록 수 |
|---|---|---|---|
| USDA FoodData Central SR Legacy | 2018-04 최종판 | 미국 농무부 공식 성분표. 2018년 이후 갱신되지 않는 과거 자료 | 30 |
| USDA FoodData Central Foundation Foods | 2026-04-30 | 미국 농무부 공식 성분표, 시료·분석법 공개 | 4 |
| 농촌진흥청 국가표준식품성분표 | 10.4판 / 2025-12-23 CSV | 한국 공식 성분표. 학명 열이 없어 식품명으로 연결 | 16 |
| 일본 식품표준성분표(MEXT) | 八訂 増補 2023 | 일본 공식 성분표 | 4 |
| 인도 식품성분표(IFCT) | 2017 | 인도 공식 성분표, 6개 지역 복합시료 | 3 |
| 독일 BLS | 4.0 (2025) | 독일 공식 DB. 수영 값은 Souci-Fachmann-Kraut(2008) 인용·환산값 | 1 |
| 학술지 논문(Molecules 2012, Foods 2021) | 2012, 2021 | 동료심사 논문. 품종 1개·한 재배지 | 5 |

## 8. 공백 목록

연결 자료가 없는 기록 69건(보류 사유는 `data/nutrition_hold_list_v1.json`):

인도아부틸론(`abutilon_indicum`), 에오니움 아르보레움(`aeonium_arboreum`), 사과나무잎(`appleleaf`), 아스틸베(`astilbe`), 강낭콩잎(`beanleaf`), 파프리카(`bellpepper`), 자작나무잎(`birchleaf`), 블랙베리잎(`blackberryleaf`), 부들레야(`buddleja_davidii`), 서양금혼초(`catsear`), 캐모마일(`chamomile`), 망초(`conyzacanadensis`), 금계국속(`coreopsis`), 코스모스(`cosmos`), 오이잎(`cucumberleaf`), 달리아(`dahlia`), 데이지(`daisy`), 아욱메풀(`dichondra_micrantha`), 에케베리아(`echeveria`), 에키네시아(`echinacea`), 느릅나무잎(`elmleaf`), 달맞이꽃(`eveningprimrose`), 톨페스큐(`fescue`), 제라늄(`geranium`), 제라늄잎(`geraniumleaf`), 거베라(`gerbera`), 은행잎(`ginkgoleaf`), 무스카리(`grapehyacinth`), 헤어벨(`harebell`), 민들레아재비류(`hawkbit`), 씀바귀아재비류(`hawksbeard`), 조밥나물류(`hawkweed`), 산사나무속 잎(`hawthorn`), 개암나무잎(`hazelleaf`), 헤지머스터드(`hedgemustard`), 광대나물(`henbit`), 무궁화꽃(`hibiscusflower`), 무궁화잎(`hibiscusleaf`), 접시꽃(`hollyhock`), 셈페르비붐(`houseleek`), 키위잎(`kiwileaf`), 흰광대나물(`lamium_album`), 라벤더(`lavender`), 레몬밤(`lemonbalm`), 피나무잎(`lindenleaf`), 단풍나무잎(`mapleleaf`), 마시멜로우(`marshmallow`), 왕포아풀(`meadowgrass`), 멕시칸페튜니아(`mexicanpetunia`), 밀크시슬(`milkthistle`), 모나르다속(`monarda`), 오레가노(`oregano`), 복숭아나무잎(`peachleaf`), 배나무잎(`pearleaf`), 페튜니아(`petunia`), 자두나무잎(`plumleaf`), 포플러잎(`poplarleaf`), 프리뮬라속(`primula`), 라즈베리잎(`raspberryleaf`), 부처스브룸(`ruscus_aculeatus`), 세이지(`sage`), 살시피류(`salsify`), 딸기잎(`strawberryleaf`), 해바라기꽃잎(`sunflowerpetal`), 제비꽃(`violet`), 제비꽃잎(`violetleaf`), 버드나무잎(`willowleaf`), 서양톱풀(`yarrow`), 백일홍(`zinnia`)

참고자료만 있는 기록 50건:

애호박잎(`aehobakleaf`), 알팔파(`alfalfa`), 보리싹(`barleygrass`), 보리잎(`barleyleaf`), 우산잔디(`bermudagrass`), 보리지(`borage`), 왕질경이(`broadleafplantain`), 메밀잎(`buckwheatleaf`), 셀러리잎(`celeryleaf`), 별꽃(`chickweed`), 클로버(`clover`), 컴프리(`comfrey`), 말바(`commonmallow`), 옥수수잎(`cornleaf`), 소리쟁이(`dock`), 넓은잎필라리(`erodium_botrys`), 펜넬잎(`fennelleaf`), 무화과잎(`figleaf`), 머루잎(`grapevineleaf`), 하와이무궁화(`hibiscusrosa`), 비비추속(`hosta`), 상추(`lettuce`), 메리골드(`marigold`), 버클로버(`medicago_hispida`), 멜론잎(`melonleaf`), 미나리(`minari`), 민트(`mint`), 귀리싹(`oatgrass`), 귀리잎(`oatleaf`), 손바닥선인장패드(`opuntiapad`), 오차드그라스(`orchard`), 천년초(`pricklypear`), 호박꽃(`pumpkinflower`), 호박잎(`pumpkinleaf`), 유채잎(`rapeseedleaf`), 레드클로버(`redclover`), 창질경이(`ribwortplantain`), 장미꽃(`rose`), 라이그라스(`ryegrass`), 샌포인(`sainfoin`), 해바라기잎(`sunflowerleaf`), 티모시(`timothy`), 등갈퀴나물(`vicia_cracca`), 살갈퀴(`vicia_sativa`), 제비꽃(`violetflower`), 미나리(`waterdropwort`), 수박잎(`watermelonleaf`), 밀싹(`wheatgrass`), 밀잎(`wheatleaf`), 화이트클로버(`whiteclover`)

검증자료가 있지만 주요 항목이 비어 있는 기록:

| 항목 | 값이 없는 검증 기록 |
|---|---|
| 식이섬유 | 콘샐러드, 질경이, 방가지똥, 쇠비름, 다채, 콩잎, 금어초, 수레국화, 한련화, 팬지, 금잔화 |
| 칼슘 | 없음 |
| 인 | 없음 |
| 수분 | 금어초, 수레국화, 한련화, 팬지, 금잔화 |

식용꽃 논문 자료는 식이섬유·수분을 측정하지 않았다. 없는 값을 0이나 추정값으로 채우지 않았다.
