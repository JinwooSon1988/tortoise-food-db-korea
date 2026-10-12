# 식물 중복·분류학 전수 검증 보고서 (2026-10-12)

대상: `data/plants.json` 182개 기록 전체. 기계 판독용 결과는 `data/plant_identity_registry_v1.json`(결정 기록)과 `data/plant_taxonomy_audit_v1.json`(자료별 원문 응답)에 있다. 이 보고서의 표는 두 파일에서 생성했다.

## 1. 요약

| 항목 | 건수 | 처리 |
|---|---|---|
| 같은 식물의 중복 등록 | 1 | 대표 ID로 데이터 통합, 기존 URL 유지 |
| 같은 학명, 다른 부위·생육 단계 | 13개 그룹 | 분리 유지(사유 기록) |
| 넓은 분류군과 좁은 분류군의 공존 | 9개 그룹 | 분리 유지(사유 기록) |
| 다른 식물의 대표 이름을 별칭으로 쓴 경우 | 4 | 수정 |
| 같은 한국어 이름을 쓰는 서로 다른 기록 | 1 | 검토 대상으로 선언 |
| 학명 처리가 자료마다 다르거나 동명이 있는 기록 | 18 | DB 표기 유지, 차이 기록 |
| 속 수준(spp.) 기록 | 42 | 변경 없음 |

학명이 같다는 이유만으로 병합한 기록은 없다. 병합(대표 ID 지정)은 이름·학명·부위·판정·근거·이미지가 모두 같은 미나리 1건뿐이다.

## 2. 사용한 분류학 자료

- GBIF Backbone Taxonomy: `api.gbif.org/v1/species/match`
- Kew WCVP(Plants of the World Online의 기반 체크리스트): GBIF에 공개된 WCVP 데이터셋(`f382f0ce-323a-4091-bb9f-add557f3a9a2`)으로 조회했다. POWO 웹사이트(`powo.science.kew.org`)는 Cloudflare 확인 화면으로 막혀 있어 직접 접근하지 않았다. 각 WCVP 기록의 POWO URL은 감사 파일에 남겼다.
- World Flora Online Plant List(분류 버전 2026-06): `list.worldfloraonline.org/matching_rest.php`, robots.txt의 요청 간격 10초 준수

## 3. 미나리 중복 정리 (`minari` / `waterdropwort`)

| 항목 | `minari` | `waterdropwort` | 판단 |
|---|---|---|---|
| 이름·학명 | 미나리 / Water dropwort / Oenanthe javanica | 같음 | 같은 식물 |
| 급여 판정 | Mediterranean_Testudo do_not_feed/C- | Mediterranean_Testudo do_not_feed/C- | 같음 |
| 학술 근거 | tortoise_table_water_dropwort_warning, lu_oenanthe_javanica_review_2019 | 같은 2건 | 같음 |
| 판정 설명 문구 | 더 상세(Oenanthe속 경고와 O. javanica 종 수준 자료 구분) | 요약형 | 문구만 다르고 결론은 같음 |
| 검증 영양자료(부위별) | RDA 10.4 물미나리 전체·잎·줄기 3건 | 없음 | minari에 유지 |
| 참고 영양자료 | 없음 | MEXT 06117, JIRCAS 2건 | **minari로 이전** |
| 이미지 | Oenanthe_javanica.JPG (CC BY-SA 3.0) | 같은 파일 | 같음 |
| 검색 별칭 | water dropwort | 미나리잎 | **minari에 병합** |
| 상세 페이지 | /plant/minari/ | /plant/waterdropwort/ | 둘 다 유지 |
| 내부 참조 | 국문 검색명 지도, 내부 링크 그래프, 블로그 딥링크 | 없음 | minari가 대표 |

**대표 ID를 `minari`로 정한 근거:** minari가 먼저 등록된 ID(기존 69종)이고, RDA 부위별 검증 기록 3건·국문 검색명 지도·내부 링크·블로그 딥링크가 minari에 연결돼 있다. 공개 목록과 검색도 minari 카드를 대표로 표시한다.

**데이터 손실 여부:** 삭제한 기록은 없다. 참고자료 2건은 `plant_id`를 `minari`로 옮기고 `legacy_plant_ids`에 `waterdropwort`를 남겼다. `plants.json`의 `waterdropwort` 행과 두 상세 페이지는 그대로 두어 기존 URL이 계속 열린다.

**정리 전 문제:** 공개 목록은 `minari` 카드만 보여 주는데 참고자료는 `waterdropwort`에만 연결돼 있어, 보이는 카드가 '영양자료 없음'으로 분류됐다. 정리 후에는 `minari` 카드가 '참고자료 있음'으로 분류된다.

**남은 일(SEO·UI 담당 영역이라 수정하지 않음):** waterdropwort 페이지의 canonical 태그를 minari로 지정하고 사이트맵·가이드 목록에서 중복 항목을 정리하는 일은 SEO·UI 담당 영역이라 수정하지 않았다.

**별도 확인된 낡은 내부 기록:** `data/blocked_food_resolution.json`, `data/review_ledger.json`, `data/review_dashboard.json`, `data/nutrition_public_status_v1.json`, `data/naver_blog_deeplinks_all_v42.json`은 미나리를 아직 '미평가(U)'로 적고 있다. 공개 판정(급여 제외)과 다르지만 공개 화면이 읽지 않는 과거 작업 파일이어서 이번에는 고치지 않고 기록만 한다.

## 4. 같은 학명, 다른 부위·생육 단계 (분리 유지)

| 학명 | 기록 | 관계 | 급여 판정 | 사유 |
|---|---|---|---|---|
| Avena sativa | 귀리싹 (`oatgrass`): young sprouts / grass stage (싹)<br>귀리잎 (`oatleaf`): leaf blades of the grown plant (잎) | same_species_different_growth_stage | Mediterranean_Testudo limited_mixed_diet/C+<br>Tortoise_general supplement_general_evidence/C+ | 싹(어린 새싹)과 다 자란 잎은 수확 단계가 다른 별도 먹이로 관리한다. 판정 범위도 다르다(싹: 지중해 Testudo, 잎: 육지거북 일반). |
| Hordeum vulgare | 보리싹 (`barleygrass`): young sprouts / grass stage (싹)<br>보리잎 (`barleyleaf`): leaf blades of the grown plant (잎) | same_species_different_growth_stage | Mediterranean_Testudo limited_mixed_diet/C+<br>Tortoise_general supplement_general_evidence/C+ | 귀리와 같은 이유로 싹과 잎을 분리한다. |
| Triticum aestivum | 밀싹 (`wheatgrass`): young sprouts / grass stage (싹)<br>밀잎 (`wheatleaf`): leaf blades of the grown plant (잎) | same_species_different_growth_stage | Mediterranean_Testudo limited_mixed_diet/C+<br>Tortoise_general supplement_general_evidence/C+ | 귀리와 같은 이유로 싹과 잎을 분리한다. |
| Brassica oleracea var. italica | 브로콜리잎 (`broccolileaf`): leaf<br>브로콜리새싹 (`broccolisprout`): sprout (seedling) | same_taxon_different_part | Tortoise_general limited/C<br>Tortoise_general do_not_feed/C+ | 새싹은 글루코시놀레이트 농도가 달라 판정이 다르다(잎: 제한 급여, 새싹: 급여 제외). |
| Cucumis sativus | 오이 (`cucumber`): fruit<br>오이잎 (`cucumberleaf`): leaf | same_taxon_different_part | Tortoise_general limited_supplement/C<br>Tortoise_general limited_supplement/C | 열매와 잎은 성분과 판정 근거가 다르다. |
| Cucurbita moschata | 애호박 (`zucchini`): immature fruit<br>애호박잎 (`aehobakleaf`): leaf | same_taxon_different_part | Tortoise_general do_not_feed/C<br>Tortoise_general limited_supplement/C | 열매(급여 제외)와 잎(제한 급여)의 판정이 다르다. |
| Cucurbita spp. | 호박잎 (`pumpkinleaf`): leaf<br>호박꽃 (`pumpkinflower`): flower | same_taxon_different_part | Tortoise_general limited_supplement/C<br>Tortoise_general limited_supplement/C | 잎과 꽃은 별도 부위다. 둘 다 속 수준 기록이다. |
| Helianthus annuus | 해바라기잎 (`sunflowerleaf`): leaf<br>해바라기꽃잎 (`sunflowerpetal`): ray-flower petals | same_taxon_different_part | Tortoise_general limited_supplement/C<br>Tortoise_general limited_supplement/C | 잎과 꽃잎은 별도 부위다. |
| Hibiscus syriacus | 무궁화잎 (`hibiscusleaf`): leaf<br>무궁화꽃 (`hibiscusflower`): flower | same_taxon_different_part | Tortoise_general supplement_general_evidence/C<br>Tortoise_general supplement_general_evidence/C | 잎과 꽃은 별도 부위다. |
| Ipomoea batatas | 고구마잎 (`sweetpotatoleaf`): leaf blade<br>고구마줄기 (`sweetpotatovine`): petiole / vine stem (줄기) | same_taxon_different_part | Tortoise_general do_not_feed/C-<br>Tortoise_general do_not_feed/C | 잎과 줄기(잎자루)는 식품성분표에서도 별도 기록이다. |
| Medicago sativa | 알팔파 (`alfalfa`): aerial forage (stems and leaves)<br>알팔파새싹 (`alfalfasprout`): sprout (seedling) | same_taxon_different_part | Mediterranean_Testudo limited_mixed_diet/B-<br>Tortoise_general do_not_feed/C+ | 새싹과 건초·생초는 성분과 판정이 다르다(새싹: 급여 제외). |
| Viola mandshurica | 제비꽃잎 (`violetleaf`): leaf<br>제비꽃 (`violetflower`): flower | same_taxon_different_part | Tortoise_general supplement_general_evidence/C+<br>Tortoise_general supplement_general_evidence/C+ | 잎과 꽃은 별도 부위다. |
| Pelargonium spp. | 제라늄 (`geranium`): whole ornamental plant, part not specified<br>제라늄잎 (`geraniumleaf`): leaf | overlapping_scope | Tortoise_general limited_supplement/C<br>Tortoise_general limited_supplement/C | 두 기록 모두 속 수준이고 판정도 같다(제한 보조 C). 부위를 특정하지 않은 '제라늄'이 '제라늄잎'을 포함하므로 사실상 중복에 가깝다. 판정 문구가 서로 달라지지 않도록 함께 검토해야 하며, 통합 여부는 별도 검토 대상이다. |

## 5. 넓은 분류군과 좁은 분류군의 공존 (분리 유지)

| 분류군 | 넓은 기록 | 좁은 기록 | 급여 판정(넓은 → 좁은) | 비고 |
|---|---|---|---|---|
| Cucurbita | 호박잎 (`pumpkinleaf`), 호박꽃 (`pumpkinflower`) | 애호박 (`zucchini`), 애호박잎 (`aehobakleaf`) | Tortoise_general limited_supplement/C / Tortoise_general limited_supplement/C → Tortoise_general do_not_feed/C / Tortoise_general limited_supplement/C | 속 수준 '호박잎·호박꽃'과 종 수준 '애호박(C. moschata)' 기록이 공존한다. 속 수준 자료를 애호박의 직접 측정값으로 쓰지 않는다. |
| Malva | 아욱 (`mallow`) | 말바 (`commonmallow`), 아욱잎 (`mallowleaf`) | Mediterranean_Testudo limited_supplement/C- → Tortoise_general supplement_general_evidence/C+ / Tortoise_general supported_mixed_diet/C | '아욱(Malva spp.)'과 '아욱잎(Malva verticillata)'은 같은 국내 채소 아욱을 가리킬 가능성이 높고 같은 RDA 식품(아욱, 생것)을 쓰지만 급여 판정이 다르다(아욱: 제한 보조 C-, 지중해 Testudo / 아욱잎: 혼합식 가능 C, 육지거북 일반). 판정 정합성 검토 대상이다. |
| Opuntia | 천년초 (`pricklypear`) | 손바닥선인장패드 (`opuntiapad`) | Tortoise_general limited_supplement/C → Tortoise_general supplement_general_evidence/C+ | '천년초(Opuntia spp.)'와 '손바닥선인장패드(O. ficus-indica)'는 종 범위가 다르다. 천년초가 어느 Opuntia 종인지 마스터에서 확정되지 않았으므로 O. ficus-indica 자료를 천년초의 직접 자료로 쓰지 않는다. |
| Plantago | 질경이 (`plantain`) | 창질경이 (`ribwortplantain`), 왕질경이 (`broadleafplantain`) | Mediterranean_Testudo limited_mixed_diet/C; Sulcata limited_mixed_diet/C → Mediterranean_Testudo limited_mixed_diet/C+ / Mediterranean_Testudo limited_mixed_diet/C | 속 수준 '질경이'와 종 수준 창질경이·왕질경이가 공존한다. 국내 표준명 질경이는 data/korea_taxon_mapping_v1.json에서 Plantago asiatica L.로 매핑돼 있다. |
| Trifolium | 클로버 (`clover`) | 화이트클로버 (`whiteclover`), 레드클로버 (`redclover`) | Mediterranean_Testudo limited_mixed_diet/B; Sulcata limited_mixed_diet/C → Mediterranean_Testudo limited_mixed_diet/C+ / Mediterranean_Testudo limited_mixed_diet/C+ | 속 수준 '클로버'와 종 수준 기록이 공존한다. |
| Viola | 제비꽃 (`violet`) | 팬지 (`pansy`), 제비꽃잎 (`violetleaf`), 제비꽃 (`violetflower`) | Tortoise_general supplement_general_evidence/C → Tortoise_general supplement_general_evidence/C / Tortoise_general supplement_general_evidence/C+ / Tortoise_general supplement_general_evidence/C+ | 속 수준 '제비꽃'과 종·잡종 수준 기록이 공존한다. |
| Beta vulgaris | 비트잎 (`beetgreens`) | 근대 (`chard`) | Tortoise_general limited_supplement/C → Tortoise_general limited_supplement/C | 비트잎(종 수준 표기)과 근대(잎채소 아종/품종군)는 같은 종의 다른 재배군이다. 성분표에서도 별도 식품이다. |
| Cichorium intybus | 치커리 (`chicory`) | 라디키오 (`radicchio`) | Mediterranean_Testudo limited_mixed_diet/B- → Mediterranean_Testudo limited_supplement/C | 치커리(종)와 라디키오(결구 적색 품종군)는 같은 종의 다른 재배군이다. |
| Lactuca sativa | 상추 (`lettuce`) | 로메인 (`romaine`) | Mediterranean_Testudo limited_supplement/C → Mediterranean_Testudo limited_supplement/C+ | 상추(종)와 로메인(품종군)은 같은 종의 다른 재배군이다. |

### 판정이 서로 다른 중복 후보: 아욱(`mallow`)과 아욱잎(`mallowleaf`)

- `data/korea_taxon_mapping_v1.json`은 `mallow`(아욱, Malva spp.)의 국내 분류군을 Malva verticillata L.로 매핑한다. `mallowleaf`의 학명도 Malva verticillata다.
- 두 기록 모두 RDA '아욱, 생것' 한 식품의 수치를 검증 영양자료로 쓴다(10.4판 F1230000000a, CSV판 R106-123000001-0000).
- 급여 판정은 다르다. `mallow`: Mediterranean_Testudo limited_supplement/C-. `mallowleaf`: Tortoise_general supported_mixed_diet/C.
- 근거도 같은 Tortoise Table Mallow 페이지를 서로 다른 근거 ID(`tortoise_table_mallow`, `tt_malva_spp_safe`)로 인용한다.
- 조치: 병합하지 않았다. 판정을 하나로 맞추려면 판정 변경이 필요하므로 `docs/FEEDING_VERDICT_EVIDENCE_WEAKNESS_20261012.md`에 변경안과 근거를 먼저 제시했다.

## 6. 이름·검색 별칭 충돌

| 기록 | 수정 전 별칭 | 수정 후 | 사유 |
|---|---|---|---|
| 밀잎 (`wheatleaf`) | 밀싹 | 밀 잎 | '밀싹'은 별도 기록 `wheatgrass`의 대표 이름이고 판정도 다르다 |
| 보리잎 (`barleyleaf`) | 보리싹 | 보리 잎 | '보리싹'은 `barleygrass`의 대표 이름 |
| 귀리잎 (`oatleaf`) | 귀리싹 | 귀리 잎 | '귀리싹'은 `oatgrass`의 대표 이름 |
| 강낭콩잎 (`beanleaf`) | 콩잎 | 강낭콩 잎 | '콩잎'은 대두 잎 기록 `soybeanleaf`의 대표 이름이고 판정도 다르다 |

수정 전에는 밀잎 상세 페이지에 '다른 이름 · 밀싹'이 표시됐다. 수정 후 다섯 개 상세 페이지(미나리 포함)의 '다른 이름' 문구만 재생성했다.

**검토 대상으로 남긴 충돌:** ko 이름 '제비꽃' — 제비꽃 (`violet`), 제비꽃 (`violetflower`). '제비꽃'이 속 수준 기록(Viola spp.)과 제비꽃 꽃 부위 기록(Viola mandshurica)의 표시명으로 함께 쓰인다. 학명이 달라 목록에 카드 두 개가 같은 이름으로 보인다. 꽃 기록의 표시명을 '제비꽃 꽃'처럼 구분하는 방안을 권고한다(페이지 제목이 바뀌므로 사이트 담당과 협의 필요).

## 7. 학명 처리가 자료마다 다른 기록

DB 학명은 바꾸지 않았다. 식품성분표와 사육자료가 쓰는 표기와 맞춰 두는 편이 출처 추적에 유리하기 때문이다. 자료별 수용명은 아래와 같다.

| 기록 | DB 학명 | GBIF | WCVP(POWO) | WFO | 결정 |
|---|---|---|---|---|---|
| 로메인 (`romaine`) | Lactuca sativa var. longifolia | lactuca sativa | 기록 없음 | lactuca sativa | GBIF와 WFO는 var. longifolia를 Lactuca sativa의 이명으로 처리한다(WCVP에는 변종 기록 없음). 로메인은 품종군으로 관리하며 종 수준 상추 기록과 구분한다. |
| 콜라드그린 (`collard`) | Brassica oleracea var. viridis | brassica oleracea | 기록 없음 | brassica oleracea, brassica oleracea viridis | 같은 품종군이 자료에 따라 다른 계급(var./subsp./f.)이나 종 수준 이명으로 처리된다. 재배 품종군 표기이므로 DB 표기를 유지한다. |
| 배추 (`napa`) | Brassica rapa subsp. pekinensis | brassica rapa | 기록 없음 | brassica rapa, brassica rapa pekinensis | 같은 품종군이 자료에 따라 다른 계급(var./subsp./f.)이나 종 수준 이명으로 처리된다. 재배 품종군 표기이므로 DB 표기를 유지한다. |
| 셀러리잎 (`celeryleaf`) | Apium graveolens | apium graveolens | apium graveolens, apium sellowianum | apium graveolens | 저자가 다른 동명(homonym)이 있어 저자 표기 없이는 한 종으로 확정되지 않는다. DB가 가리키는 이름은 아래 intended_name이다. 의도한 이름: Apium graveolens L. |
| 별꽃 (`chickweed`) | Stellaria media | stellaria media | stellaria media, stellaria palustris | stellaria media | 저자가 다른 동명(homonym)이 있어 저자 표기 없이는 한 종으로 확정되지 않는다. DB가 가리키는 이름은 아래 intended_name이다. 의도한 이름: Stellaria media (L.) Vill. |
| 딜 (`dill`) | Anethum graveolens | anethum graveolens | anethum graveolens, ridolfia segetum | anethum graveolens, ridolfia segetum | 저자가 다른 동명(homonym)이 있어 저자 표기 없이는 한 종으로 확정되지 않는다. DB가 가리키는 이름은 아래 intended_name이다. 의도한 이름: Anethum graveolens L. |
| 근대 (`chard`) | Beta vulgaris subsp. cicla | beta vulgaris vulgaris | 기록 없음 | beta vulgaris | GBIF는 subsp. cicla를 Beta vulgaris subsp. vulgaris의 이명으로, WFO는 Beta vulgaris의 이명으로 처리한다. USDA도 근대를 subsp. vulgaris로 표기한다. 근대는 잎채소 품종군으로 관리하며 비트잎 기록과 구분한다. |
| 콘샐러드 (`lambs_lettuce`) | Valerianella locusta | valerianella locusta | valeriana locusta | valeriana locusta | WCVP와 WFO는 Valerianella locusta를 Valeriana locusta L.로 옮겼고 GBIF는 Valerianella locusta를 유지한다. 자료 간 불일치이므로 DB 표기를 유지한다. |
| 라벤더 (`lavender`) | Lavandula angustifolia | lavandula angustifolia | lavandula angustifolia, lavandula latifolia | lavandula angustifolia, lavandula latifolia | 저자가 다른 동명(homonym)이 있어 저자 표기 없이는 한 종으로 확정되지 않는다. DB가 가리키는 이름은 아래 intended_name이다. 의도한 이름: Lavandula angustifolia Mill. |
| 블랙베리잎 (`blackberryleaf`) | Rubus fruticosus agg. | rubus fruticosus | rubus fruticosus | rubus fruticosus, rubus vestitus | 저자가 다른 동명(homonym)이 있어 저자 표기 없이는 한 종으로 확정되지 않는다. DB가 가리키는 이름은 아래 intended_name이다. 의도한 이름: Rubus fruticosus L. |
| 명아주 (`lambsquarters`) | Chenopodium album | chenopodium album | chenopodium album, chenopodium berlandieri boscianum | chenopodium album | 저자가 다른 동명(homonym)이 있어 저자 표기 없이는 한 종으로 확정되지 않는다. DB가 가리키는 이름은 아래 intended_name이다. 의도한 이름: Chenopodium album L. |
| 소리쟁이 (`dock`) | Rumex crispus | rumex crispus | rumex crispus, rumex trisetifer | rumex crispus | 저자가 다른 동명(homonym)이 있어 저자 표기 없이는 한 종으로 확정되지 않는다. DB가 가리키는 이름은 아래 intended_name이다. 의도한 이름: Rumex crispus L. |
| 완두순 (`peashoot`) | Pisum sativum | lathyrus oleraceus | lathyrus oleraceus | lathyrus oleraceus | GBIF·WCVP·WFO 모두 Pisum sativum을 Lathyrus oleraceus Lam.의 이명으로 처리한다. 식품성분표(MEXT, USDA)와 사육자료는 여전히 Pisum sativum을 쓰므로 DB 표기는 유지하고 현재 수용명을 함께 기록한다. |
| 미즈나 (`mizuna`) | Brassica rapa var. nipposinica | brassica rapa | 기록 없음 | brassica rapa, brassica rapa nipposinica | 같은 품종군이 자료에 따라 다른 계급(var./subsp./f.)이나 종 수준 이명으로 처리된다. 재배 품종군 표기이므로 DB 표기를 유지한다. |
| 다채 (`tatsoi`) | Brassica rapa subsp. narinosa | brassica rapa | 기록 없음 | brassica rapa, brassica rapa narinosa | 같은 품종군이 자료에 따라 다른 계급(var./subsp./f.)이나 종 수준 이명으로 처리된다. 재배 품종군 표기이므로 DB 표기를 유지한다. |
| 코마츠나 (`komatsuna`) | Brassica rapa var. perviridis | brassica rapa | 기록 없음 | brassica rapa oleifera | GBIF는 var. perviridis를 Brassica rapa로, WFO는 Brassica rapa subsp. oleifera로 처리한다. 자료마다 다르므로 DB 표기를 유지한다. |
| 키위잎 (`kiwileaf`) | Actinidia deliciosa | actinidia chinensis deliciosa | actinidia chinensis deliciosa | actinidia chinensis deliciosa | 세 자료 모두 Actinidia deliciosa를 Actinidia chinensis var. deliciosa의 이명으로 처리한다. 종 수준 자료를 찾을 때 A. chinensis 자료와 혼동하지 않도록 변종 수준 표기를 함께 기록한다. |
| 톨페스큐 (`fescue`) | Schedonorus arundinaceus | lolium arundinaceum, scolochloa festucacea | lolium arundinaceum, scolochloa festucacea | lolium arundinaceum, scolochloa festucacea | Schedonorus arundinaceus는 저자가 다른 두 이름이 있다. DB가 가리키는 톨페스큐는 Schedonorus arundinaceus (Schreb.) Dumort.이며 세 자료 모두 Lolium arundinaceum (Schreb.) Darbysh.의 이명으로 처리한다. 다른 하나(Roem. & Schult.)는 Scolochloa festucacea의 이명이다. 저자 표기가 없으면 GBIF가 종을 확정하지 못한다. 의도한 이름: Schedonorus arundinaceus (Schreb.) Dumort. |

한 자료만 다르게 처리하는 기록(참고):

- 라디키오 (`radicchio`) `Cichorium intybus var. foliosum`: GBIF → cichorium intybus foliosum; WCVP → 없음; WFO → cichorium intybus
- 케일 (`kale`) `Brassica oleracea var. sabellica`: GBIF → brassica oleracea; WCVP → 없음; WFO → brassica oleracea sabellica
- 청경채 (`bokchoy`) `Brassica rapa subsp. chinensis`: GBIF → brassica rapa; WCVP → 없음; WFO → brassica rapa chinensis
- 갓 (`mustard`) `Brassica juncea`: GBIF → brassica juncea; WCVP → brassarda juncea; WFO → brassica juncea
- 양배추 (`cabbage`) `Brassica oleracea var. capitata`: GBIF → brassica oleracea; WCVP → 없음; WFO → brassica oleracea capitata
- 무잎 (`radishgreens`) `Raphanus sativus`: GBIF → raphanus sativus; WCVP → raphanus raphanistrum sativus; WFO → raphanus sativus
- 브로콜리잎 (`broccolileaf`) `Brassica oleracea var. italica`: GBIF → brassica oleracea; WCVP → 없음; WFO → brassica oleracea italica
- 콜리플라워잎 (`cauliflowerleaf`) `Brassica oleracea var. botrytis`: GBIF → brassica cretica cretica; WCVP → 없음; WFO → brassica oleracea botrytis
- 브로콜리새싹 (`broccolisprout`) `Brassica oleracea var. italica`: GBIF → brassica oleracea; WCVP → 없음; WFO → brassica oleracea italica
- 콜라비잎 (`kohlrabileaf`) `Brassica oleracea var. gongylodes`: GBIF → brassica oleracea; WCVP → 없음; WFO → brassica oleracea gongylodes

WCVP에 해당 종내 분류군(변종·아종) 기록이 없는 것은 17건이며 모두 재배 작물의 변종·아종 표기다: `romaine`, `radicchio`, `kale`, `bokchoy`, `turnipgreens`, `collard`, `cabbage`, `napa`, `broccolileaf`, `cauliflowerleaf`, `carrottop`, `chard`, `broccolisprout`, `kohlrabileaf`, `mizuna`, `tatsoi`, `komatsuna`.

## 8. 권고

1. 동명이 있는 종(셀러리, 별꽃, 딜, 라벤더, 명아주, 소리쟁이, 톨페스큐 등)은 `plants.json` 학명에 저자 표기를 추가하면 자동 대조가 한 종으로 확정된다.
2. 완두순·키위잎·콘샐러드처럼 현재 수용명이 바뀐 종은 수용명을 검색 별칭이나 분류 메모로 추가하는 방안을 검토한다(표시 문구가 바뀌므로 이번에는 하지 않았다).
3. 제라늄/제라늄잎, 아욱/아욱잎은 통합 여부를 결정해야 한다. 아욱은 판정 조정이 선행돼야 한다.
4. 새 식물을 추가하면 `scripts/build_plant_taxonomy_audit_v1.py`를 다시 실행해야 CI(`qa_plant_identity_v1.py`)가 통과한다.
