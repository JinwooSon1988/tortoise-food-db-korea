# 근거가 취약한 급여 판정 목록 (2026-10-12)

기계 판독용 결과: `data/feeding_evidence_strength_audit_v1.json` (`scripts/build_feeding_evidence_strength_audit_v1.py`로 생성). 이 작업에서 급여 판정·등급·신뢰도는 바꾸지 않았다.

판정의 확실성(신뢰도 등급)과 근거의 직접성(어떤 종류의 연구인가)은 별개 항목으로 집계했다.

## 1. 판정 186건이 기대는 가장 직접적인 근거

| 근거 종류 | 판정 수 | 신뢰도 분포 |
|---|---|---|
| 판정 대상 육지거북 분류군을 직접 다룬 연구 | 9 | A 1, B 4, B+ 1, B- 2, C 1 |
| 다른 육지거북 종을 다룬 연구 | 1 | C- 1 |
| 사육 경험·전문가 권고(전문 식물 DB, 사육 지침, 수의 편람) | 170 | B 4, C 113, C+ 46, C- 6, D+ 1 |
| 포유류 등 다른 동물·세포 연구 | 3 | C 1, C- 2 |
| 영양성분·분류 확인 자료(급여 근거 아님) | 3 | C 3 |

판정 186건 중 176건은 육지거북을 직접 다룬 연구가 하나도 연결돼 있지 않다. 대부분 전문 사육자료 한 곳(주로 The Tortoise Table)의 분류에 기댄다.

## 2. 취약 등급

| 등급 | 기준 | 판정 수 |
|---|---|---|
| A | 육지거북 급여를 다룬 자료가 하나도 없음 | 6 |
| B | 신뢰도가 B 이상인데 육지거북 연구가 없음 | 4 |
| C | 육지거북 관련 자료가 전문 사육자료 1건뿐 | 148 |
| 해당 없음 | | 28 |

## 3. A·B 등급 판정과 변경안

아래 변경안은 **적용하지 않았다**. 판정이나 신뢰도를 바꾸려면 승인이 필요하다.

| 등급 | 식물 | 현재 판정 / 신뢰도 | 연결된 근거 | 변경안과 이유 |
|---|---|---|---|---|
| A | 메밀잎 (`buckwheatleaf`) | do_not_feed / C | buckwheat_leaf_fagopyrin_2019 (영양성분·분류 확인 자료; Plant composition) | 판정(급여 제외)은 보수적 위험관리로 유지 가능. 다만 근거가 식물 성분 논문 1건뿐이므로 신뢰도를 C에서 C-로 낮추고 '육지거북 자료 없음'을 표시하는 안. |
| B | 헤지머스터드 (`hedgemustard`) | limited_mixed_diet / B | tortoise_trust_hedge_mustard (사육 경험·전문가 권고; Tortoise general)<br>kew_sisymbrium_officinale_taxonomy (영양성분·분류 확인 자료; not_applicable)<br>ttable_sisymbrium_officinale_712 (사육 경험·전문가 권고; Tortoise general)<br>sisymbrium_itc_2021 (영양성분·분류 확인 자료; not_applicable) | 근거는 전문 사육자료 2곳이고 육지거북 연구는 없다. 같은 수준의 근거를 가진 다른 판정은 C~C+이므로 신뢰도 B를 C+로 맞추는 안. |
| B | 흰광대나물 (`lamium_album`) | supported_mixed_diet / B | ttable_lamium_album_774 (사육 경험·전문가 권고; Tortoise general)<br>ttrust_lamium_album (사육 경험·전문가 권고; Tortoise general / Testudo context) | 위와 같음. 전문 사육자료 2곳 근거이므로 신뢰도 B를 C+로 맞추는 안. |
| B | 살갈퀴 (`vicia_sativa`) | limited_mixed_diet / B | ttable_vicia_310 (사육 경험·전문가 권고; Tortoise general)<br>tortoiseclub_vicia_sativa_mix (사육 경험·전문가 권고; Tortoise general) | 위와 같음. 전문 DB 1곳과 종자 혼합 제품 안내 1곳이 근거다. 신뢰도 B를 C+로 맞추는 안. |
| B | 등갈퀴나물 (`vicia_cracca`) | limited_mixed_diet / B | ttable_vicia_310 (사육 경험·전문가 권고; Tortoise general)<br>naturescape_nt_tortoise_mix (사육 경험·전문가 권고; Tortoise general) | 위와 같음. 전문 DB 1곳과 종자 혼합 제품 안내 1곳이 근거다. 신뢰도 B를 C+로 맞추는 안. |
| A | 마시멜로우 (`marshmallow`) | do_not_feed / C- | vetpharm_althaea_officinalis (포유류 등 다른 동물·세포 연구; Animals general)<br>althaea_carp_toxicology_2016 (포유류 등 다른 동물·세포 연구; Cyprinus carpio) | 급여 제외 유지. 근거는 수의독성 DB(동물 일반)와 잉어 추출물 연구이며 육지거북 자료가 없다는 점을 판정 문구가 이미 밝히고 있어 변경 불필요. |
| A | 키위잎 (`kiwileaf`) | do_not_feed / C- | actinidia_deliciosa_leaf_genotoxicity_2026 (포유류 등 다른 동물·세포 연구; Chinese hamster ovary cells; in vitro)<br>actinidia_iridoid_distribution_2023 (포유류 등 다른 동물·세포 연구; Cats and plant chemistry)<br>actinidia_leaf_calcium_oxalate_1987 (영양성분·분류 확인 자료; Plant chemistry)<br>actinidia_leaf_phytotoxicity_2019 (영양성분·분류 확인 자료; Plant bioassays) | 급여 제외 유지. 세포 실험과 성분 자료뿐이며 신뢰도 C-가 근거 수준과 맞는다. |
| A | 왕포아풀 (`meadowgrass`) | limited_mixed_diet / C | kew_poa_pratensis_identity (영양성분·분류 확인 자료; Not applicable)<br>kew_poa_pratensis_animal_food (영양성분·분류 확인 자료; Not applicable) | '제한 혼합식'이라는 긍정 판정의 근거가 Kew 분류 확인 페이지 1곳(같은 URL을 근거 2건으로 등록)뿐이다. 육지거북 급여 자료가 확보될 때까지 '판정 보류(근거 부족)'로 바꾸는 안. |
| A | 비름 (`amaranthleaf`) | limited_supplement / C | prakash_amaranthus_leaves_1991 (영양성분·분류 확인 자료; Plant composition) | '제한 보조' 판정의 근거가 식물 성분 논문 1건뿐이다. 전문 사육자료의 비름속 분류를 확인해 근거로 연결하거나, 확인 전까지 '판정 보류'로 바꾸는 안. |
| A | 콩잎 (`soybeanleaf`) | limited_supplement / C | soybean_leaf_nutrition_2026 (포유류 등 다른 동물·세포 연구; Clanis bilineata tsingtauica larvae; leaf composition)<br>soybean_leaf_trypsin_1987 (포유류 등 다른 동물·세포 연구; Plant chemistry; Mexican bean beetle herbivory) | '제한 보조' 판정의 근거가 곤충 사료 연구와 잎 성분 연구뿐이다. 육지거북 급여 자료가 없으므로 '판정 보류'로 바꾸는 안. |

## 4. 같은 식물인데 판정이 다른 경우: 아욱과 아욱잎

- `mallow`(아욱, Malva spp.): Mediterranean_Testudo limited_supplement/C-. 근거는 Tortoise Table Mallow(Malva spp. 급여 가능)와 Testudo 사육자료.
- `mallowleaf`(아욱잎, Malva verticillata): Tortoise_general supported_mixed_diet/C. 근거는 같은 Tortoise Table Mallow 페이지 1건.
- 저장소의 국내 분류군 매핑은 아욱을 Malva verticillata로 확정했다. 그런데 `mallow`의 판정 문구는 '국내 아욱이 Malva 분류군과 일치하는지 종 수준 확인이 더 필요하다'며 판정을 낮춰 두었다. 매핑이 끝난 지금은 이 전제가 맞지 않는다.
- 변경안(미적용): 두 기록의 판정을 하나로 맞춘다. 근거가 둘 다 속 수준 전문 사육자료이므로 `mallowleaf`의 판정·신뢰도(혼합식 가능, C)로 통일하고 `mallow`를 `mallowleaf`의 대표 기록으로 정리하는 안이 근거와 가장 잘 맞는다. 반대로 `mallow` 쪽으로 낮추려면 M. verticillata에 대한 위험 근거가 필요하나 현재 그런 근거는 연결돼 있지 않다.

## 5. 근거 레코드 자체의 문제

| 문제 | 건수 |
|---|---|
| 같은 출처 URL이 근거 레코드 여러 개로 등록됨 | URL 15개 (레코드 34건) |
| 한 판정이 같은 출처를 두 번 인용 | 4 |
| 어떤 판정도 인용하지 않는 근거 레코드 | 3 |
| 식물별 페이지가 아닌 목록·검색 페이지를 가리키는 레코드 | 13 |

같은 출처를 여러 번 등록하면 근거 수가 실제보다 많아 보인다. 판정 화면의 '근거 n건'을 해석할 때 주의가 필요하다.

중복 등록된 출처:

- https://doi.org/10.1016/j.foodcont.2024.110930 — `sattler_borage_pa_2025`, `sattler_borago_pa_2025`
- https://pmc.ncbi.nlm.nih.gov/articles/pmc8257512 — `ceccanti_rumex_oxalate_2021`, `di_noia_rumex_oxalate_2021`, `rumex_acetosa_oxalate_2021`
- https://powo.science.kew.org/taxon/417792-1 — `kew_poa_pratensis_animal_food`, `kew_poa_pratensis_identity`
- https://pubmed.ncbi.nlm.nih.gov/33003576 — `piatczak_salix_alba_leaf_2020`, `piatczak_salix_alba_leaf_phenolics_2020`
- https://pubmed.ncbi.nlm.nih.gov/36924638 — `sattler_borage_pa_2023`, `sattler_borago_pa_2023`
- https://www.thetortoisetable.org.uk/plant-database/viewplants/?c=6&plant=736 — `tortoise_table_harebell`, `ttable_campanula_rotundifolia_736`
- https://www.thetortoisetable.org.uk/plant-database/viewplants/?plant=313 — `tortoise_table_calendula`, `tortoise_table_calendula_current`
- https://www.thetortoisetable.org.uk/plant-database/viewplants/?plant=622 — `tortoise_table_broccoli`, `tt_broccoli_622`
- https://www.thetortoisetable.org.uk/plant-database/viewplants/?plant=624 — `tt_melon_624`, `tt_watermelon_624`
- https://www.thetortoisetable.org.uk/plant-database/viewplants/?plant=627 — `tortoise_table_squash_courgette`, `tortoise_table_squash_cucurbita_moschata`
- https://www.thetortoisetable.org.uk/plant-database/viewplants/a-z/?l=h — `tortoise_table_hawkbit`, `tortoise_table_hawkweed`, `tortoise_table_hibiscus_rosa`
- https://www.thetortoisetable.org.uk/plant-database/viewplants/colour/?colour=all — `tortoise_table_cornflower`, `tortoise_table_cosmos`
- https://www.thetortoisetable.org.uk/plant-database/viewplants/search/?searchchoice=anywords&searchtxt=apple+tree+with+apples — `tortoise_table_peach_tree`, `tortoise_table_pear_tree`
- https://www.tortoisetrust.org/articles/basicmedfood.htm — `tortoise_trust_mediterranean_grass_context`, `tt_mediterranean_food`
- https://www.tortoisetrust.org/articles/plantfoods.html — `tortoise_trust_hedge_mustard`, `tt_plantfoods`, `ttrust_lamium_album`, `ttrust_sisymbrium_officinale`

목록·검색 페이지를 가리키는 레코드: `tortoise_table_apple_tree`, `tortoise_table_birch`, `tortoise_table_cornflower`, `tortoise_table_cosmos`, `tortoise_table_echinacea`, `tortoise_table_ginkgo`, `tortoise_table_hawkbit`, `tortoise_table_hawkweed`, `tortoise_table_hibiscus_rosa`, `tortoise_table_lavender`, `tortoise_table_peach_tree`, `tortoise_table_pear_tree`, `tt_malva_spp_safe`.

인용되지 않는 레코드: `tortoise_table_calendula`, `ttable_campanula_rotundifolia_736`, `ttrust_sisymbrium_officinale`.

## 6. C 등급(전문 사육자료 1건) 판정 148건

판정별 근거는 JSON 파일에 있다. 식물 목록:

- **do_not_feed** (34): 고구마잎, 셀러리잎, 시금치, 파슬리, 미나리, 미나리, 고구마줄기, 완두순, 서양톱풀, 쇠비름, 데이지, 수영, 소리쟁이, 명아주, 콜라비잎, 무스카리, 버드나무잎, 포플러잎, 숙주나물, 산사나무속 잎, 보리지, 프리뮬라속, 컴프리, 알팔파새싹, 무화과잎, 애호박, 파프리카, 깻잎, 메리골드, 토마토, 쑥, 브로콜리새싹, 망초, 자두나무잎
- **general_reptile_supplement** (4): 청경채, 콜라드그린, 양배추, 갓
- **limited** (2): 브로콜리잎, 콜리플라워잎
- **limited_mixed_diet** (16): 별꽃, 별꽃, 무잎, 레드클로버, 창질경이, 왕질경이, 유채잎, 강낭콩잎, 국화, 미즈나, 다채, 코마츠나, 헤어벨, 인도아부틸론, 에오니움 아르보레움, 부들레야
- **limited_supplement** (57): 라디키오, 장미꽃, 물냉이, 천년초, 호박잎, 포도잎, 한련화, 순무잎, 배추, 루꼴라, 비트잎, 고수, 딜, 근대, 민트, 제라늄잎, 오이잎, 머루잎, 해바라기꽃잎, 호박꽃, 레몬밤, 캐모마일, 수레국화, 라벤더, 코스모스, 사과나무잎, 펜넬잎, 딸기잎, 세이지, 은행잎, 피나무잎, 자작나무잎, 로즈마리, 배나무잎, 복숭아나무잎, 블랙베리잎, 단풍나무잎, 개암나무잎, 밀크시슬, 샌포인, 광대나물, 비비추속, 조밥나물류, 냉이, 페튜니아, 달리아, 거베라, 멜론잎, 수박잎, 당근잎, 오이, 바질, 애호박잎, 쑥갓, 제라늄, 해바라기잎, 옥수수잎
- **supplement_general_evidence** (31): 뽕잎, 무궁화잎, 무궁화꽃, 콘샐러드, 제비꽃잎, 제비꽃, 손바닥선인장패드, 밀잎, 보리잎, 접시꽃, 에키네시아, 하와이무궁화, 오레가노, 타임, 느릅나무잎, 달맞이꽃, 셈페르비붐, 에케베리아, 금어초, 살시피류, 씀바귀아재비류, 민들레아재비류, 서양금혼초, 백일홍, 멕시칸페튜니아, 금계국속, 아스틸베, 모나르다속, 금잔화, 팬지, 제비꽃
- **supported_mixed_diet** (4): 톨페스큐, 아욱잎, 넓은잎필라리, 아욱메풀

## 7. 육지거북 연구가 연결된 판정 10건

- 민들레 (`dandelion`) — Mediterranean_Testudo, supported_mixed_diet / B+: iftime_ibera_dobrogea_2012 (Testudo graeca ibera), mitrevichin_ibera_bulgaria_2023 (Testudo graeca ibera)
- 질경이 (`plantain`) — Mediterranean_Testudo, limited_mixed_diet / C: hermanni_foraging_italy_2015 (Testudo hermanni)
- 방가지똥 (`sowthistle`) — Mediterranean_Testudo, supported_mixed_diet / B: iftime_ibera_dobrogea_2012 (Testudo graeca ibera), ibera_eastern_account_2023 (Testudo graeca ibera and eastern Testudo graeca clades)
- 클로버 (`clover`) — Mediterranean_Testudo, limited_mixed_diet / B: iftime_ibera_dobrogea_2012 (Testudo graeca ibera), ibera_eastern_account_2023 (Testudo graeca ibera and eastern Testudo graeca clades), hermanni_foraging_italy_2015 (Testudo hermanni)
- 알팔파 (`alfalfa`) — Mediterranean_Testudo, limited_mixed_diet / B-: iftime_ibera_dobrogea_2012 (Testudo graeca ibera), mitrevichin_ibera_bulgaria_2023 (Testudo graeca ibera), ibera_eastern_account_2023 (Testudo graeca ibera and eastern Testudo graeca clades), tgraeca_alfalfa_context_2019 (Testudo graeca)
- 돌나물 (`dolnamul`) — Tortoise_general, limited_supplement / C-: mitrevichin_ibera_bulgaria_2023 (Testudo graeca ibera)
- 치커리 (`chicory`) — Mediterranean_Testudo, limited_mixed_diet / B-: mitrevichin_ibera_bulgaria_2023 (Testudo graeca ibera)
- 우산잔디 (`bermudagrass`) — Mediterranean_Testudo, supported_mixed_diet / A: testudo_graeca_cynodon_field_diet_2008 (Testudo graeca), chersina_cynodon_field_diet (Chersina angulata)
- 버클로버 (`medicago_hispida`) — Mediterranean_Testudo, limited_mixed_diet / B: wild_medicago_polymorpha_tgg_morocco (Testudo graeca graeca)
- 부처스브룸 (`ruscus_aculeatus`) — Mediterranean_Testudo, limited_mixed_diet / B: wild_ruscus_aculeatus_thh_italy_2011 (Testudo hermanni hermanni)

이 연구들은 대부분 야생 섭식 관찰이다. 야생에서 먹었다는 기록은 사육 급여량이나 장기 안전성을 정해 주지 않는다.
