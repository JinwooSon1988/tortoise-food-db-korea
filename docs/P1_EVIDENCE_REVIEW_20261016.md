# P1 학술 검토와 사과나무잎 주의 보강 (2026-10-16)

PR #315 검증의 수동 검토 목록(69개 단위) 가운데 P1 15건을 원문과 다시 대조했다.

- 이 문서와 이 PR은 급여 등급·근거 확실성을 하나도 바꾸지 않는다.
- 바꾸는 것은 사과나무잎의 한계 1줄과 그 영어 번역뿐이다(5절).

**근거 수준 표기:**
- **원문 열람:** 2026-10-16에 해당 페이지를 직접 받아 읽음.
- **저장소 기록:** 저장소 기록만 확인함.

## 1. 아욱잎 `mallowleaf` (A / C) — HOLD, 소유자 결정 필요

**원문 열람:** https://www.thetortoisetable.org.uk/plant-database/viewplants/?plant=363
- "Mallow", Latin Name "Malva spp.", Safe to Feed.
- "All tortoises enjoy a snack on mallow flowers and leaves and you can find it growing almost all year round."
- *Malva verticillata*라는 이름은 없다.

**같은 원문을 쓰는 세 판정이 서로 맞지 않는다.**

| 식물 | 학명 | 판정 / 확실성 | 이 원문 기록의 directness |
|---|---|---|---|
| 아욱 `mallow` | *Malva* spp. | C / C- (지중해 Testudo) | contextual (`tortoise_table_mallow`) |
| 말바 `commonmallow` | *Malva sylvestris* | C / C+ | contextual (`tortoise_table_mallow`) |
| 아욱잎 `mallowleaf` | *Malva verticillata* | **A / C** | **expert_husbandry** (`tt_malva_spp_safe`) |

- 같은 페이지(`source_id` `thetortoisetable:plant=363`)를 기록 두 개로 나눴고, 근거 성격을 서로 다르게 분류했다.
- 속 수준 원문 하나에 기대는 판정 가운데, 학명이 가장 좁은(원문에 이름이 없는) 아욱잎이 가장 높은 등급을 받았다.

**위험 근거는 없다.** 근거가 부족하다는 사실만으로 등급을 내리면, 근거 부족을 위험 신호로 취급하게 된다.

**선택지:**
- (a) **현행 유지 (A / C).** 판정 설명이 이미 "종 수준 직접 근거 없음, 원문은 속 전체"를 밝힌다(#315).
- (b) **등급 A 유지, 확실성만 C-로.** 근거가 속 수준 원문 1곳이고 종 이름이 없다는 점을 확실성에 반영한다. 등급 의미는 바뀌지 않는다.
- (c) **권고: 아욱·아욱잎·말바를 한 번에 결정한다.**
  - 먼저 같은 원문 기록 두 개의 directness를 하나로 맞춘다. contextual과 expert_husbandry 가운데 하나다.
  - 다음 규칙 하나로 세 판정을 다시 본다: "원문이 속만 다루고 종 이름이 없을 때 최고 등급과 확실성은 얼마인가."
  - #287의 `mallow`/`mallowleaf` 제안과 같은 결정이다.

## 2. 멜론잎·수박잎 (C / C+) — 제안 철회 유지

**원문 열람:** https://www.thetortoisetable.org.uk/plant-database/viewplants/?plant=624
- "Melon (Cantaloupe, Muskmelon, Watermelon, Ogen Melon, Honeydew, Galia)", Latin Name "Citrullus lanatis spp., Cucumis melo spp.", Feed Sparingly.
- "The leaves and flowers of melons can be nibbled, but should be fed sparingly."

**결론:**
- 두 판정이 같은 원문 한 문장을 공유한다. #315가 이 사실을 한·영 판정 설명과 근거 카드에 공개했으므로 그대로 둔다.
- C+→C 제안은 철회한다. 단일 전문 DB 항목 판정 65건 가운데 C+가 24건이라, 두 판정만 낮추면 기준이 어긋난다.

## 3. 나머지 P1 13건

| 판정 | 원문 열람 결과 | 판단 | 권고 |
|---|---|---|---|
| 보리싹·밀싹 (B / C+) | Cat Grass (https://www.thetortoisetable.org.uk/plant-database/viewplants/?plant=687): "Barley Grass (Hordeum spp.)", "Wheat Grass (Triticum spp.)"를 이름으로 든다. "the young grasses can be fed", 성숙한 씨앗은 단백질이 많아 먹이지 않는다. Safe to Feed. | 원문이 두 식물을 속 수준으로 이름을 들어 다룬다. 부위(어린 풀)도 맞다. | 등급 유지. P3로 내림. |
| 왕질경이 *Plantago major* (B / C) | Tortoise Trust (https://www.tortoisetrust.org/articles/plantfoods.html): 권장 기본 먹이 "Plantains (Plantago spp.)". 별도 목록은 "Greater Plantain (Plantago media)"이다. 일반명은 *P. major*, 학명은 *P. media*로 원문 안에서 어긋난다. | 속 수준 근거만 확실하다. 종 수준 연결은 원문 표기 오류 때문에 확정할 수 없다. | 등급 유지. 근거 기록에 식물별 범위("Plantago spp.; 'Greater Plantain'을 Plantago media로 표기")를 적는다. P1 유지. |
| 별꽃 *Stellaria media* (B / C, 지중해·설가타) | BCG 지중해·설가타 사육 안내(https://archive.britishcheloniagroup.org.uk/caresheets/caremed, …/sulcata)는 "chickweed" 일반명만 든다. 같은 판정이 쓰지 않는 Tortoise Trust 페이지는 "Chickweed (Stelaria media)"로 종 수준 이름을 든다. | 종 수준 근거가 저장소의 다른 기록에 있다. 지금 판정은 일반명 자료만 연결한다. | Tortoise Trust 기록 연결 검토(소유자 확인 후 별도 PR). 등급 유지. |
| 국화 *Chrysanthemum morifolium* (B / C+) | Chrysanthemum (https://www.thetortoisetable.org.uk/plant-database/viewplants/?plant=94): *Chrysanthemum* spp., Feed in Moderation. "most species … in moderate or small quantities". 제충국 2종(*C. cinerariifolium*, *C. coccineum*)만 제외한다. "if in doubt do not feed". | 속 수준이다. 재배 국화 이름은 없지만 제외 종을 명시한다. | 아욱잎과 같은 "속 수준 원문, 종 이름 없음" 규칙으로 함께 결정(1절 c). |
| 파프리카 *Capsicum annuum* (D / C) | Sweet Pepper (Green Pepper, Pepper, Capsicum, Bell Pepper) (https://www.thetortoisetable.org.uk/plant-database/viewplants/?plant=632): *Capsicum* spp., Do not Feed. 열매 자체는 독성이 없고 소량은 해롭지 않다. 잎·줄기·뿌리는 독성. Ca:P 1:2.1, 익은 열매는 당이 많다. | 원문 일반명이 "Bell Pepper"라 대상이 분명하다. D(계획 급여 제외)의 이유는 독성이 아니라 영양 균형과 당이다. 공개 문구도 독성을 확정하지 않는다(#315 검증). | 유지. |
| 미나리 `minari`·`waterdropwort` (D / C-) | 연결 페이지(https://www.thetortoisetable.org.uk/plant-database/viewplants/?c=6&plant=828)는 Oenanthe가 아니라 **Dropwort (*Filipendula vulgaris*), Feed Sparingly** 항목이다. 그 안에 "Do not confuse with any of Water Dropworts of the Oenanthe genus … highly toxic (especially the Hemlock Water Dropwort) and should be avoided at all costs"라는 상호 참조 경고가 있다. A–Z 목록에 Oenanthe 항목은 없다. | 근거 기록의 `supports`는 이 점("Filipendula dropwort와 다른 Oenanthe water dropwort")을 정확히 적었다. Feed Sparingly 분류는 Filipendula의 것이며, 미나리 판정에 쓰이지 않았다. | 유지. 국내 *O. javanica*의 종 수준 자료 탐색은 계속 과제로 둔다. |
| 숙주나물 *Vigna radiata* (D / C) | Bean Sprouts (https://www.thetortoisetable.org.uk/plant-database/viewplants/?plant=812): Latin Name "Vigna radiata; Glycine max", Do not Feed. 녹두·대두 싹은 단백질이 많고 피트산이 칼슘 흡수에 영향을 준다. "they aren't toxic or poisonous in any way". | 묶음 항목이지만 원문이 *V. radiata*를 이름으로 들고, 이유도 두 콩에 함께 적용한다. D의 이유는 독성이 아니다. | 유지. P3로 내림. |
| 깻잎 *Perilla frutescens* (D / C+) | Perilla (Beefsteak Plant, Purple Mint, Shiso) (https://www.thetortoisetable.org.uk/plant-database/viewplants/?plant=507): *Perilla* spp., Do not Feed. 원인 물질을 "perillaldehyd"로 적는다. 소·말에서 폐부종·호흡부전. | 원문의 원인 물질 표기는 부정확하다. 소의 폐독성 원인은 페릴라케톤이다(연결 원논문 Kerr 1986, PMID 3776081). 공개 판정은 원문 표기를 따르지 않고 페릴라케톤으로 바르게 쓴다. | 유지. |
| 쑥 *Artemisia princeps* (D / C-) | Mugwort (Common Wormwood) (https://www.thetortoisetable.org.uk/plant-database/viewplants/?plant=502): *Artemisia* spp., Do not Feed. 원인 물질은 투존이다. | 속 수준 경고다. *A. princeps* 잎에서 알파-투존을 주요 휘발 성분으로 측정한 원논문이 따로 연결돼 있다(종 수준 성분 근거). | 유지. |

## 4. P1 재분류 요약
- **P1 유지 (6):**
  - 아욱잎: 소유자 결정
  - 국화: 아욱잎과 같은 규칙
  - 왕질경이: 원문 학명 표기 오류
  - 별꽃 2건: 종 수준 기록 연결 검토
  - 멜론·수박잎: 공통 원문 공개 완료, 확실성 기준 과제
- **P3로 내림 (3):**
  - 보리싹·밀싹: 원문이 이름을 들어 다룸
  - 숙주나물: 원문이 *V. radiata*를 명시
- **유지, 추가 조치 없음 (6):**
  - 파프리카
  - 미나리 2판정
  - 깻잎
  - 쑥
  - 사과나무잎: 5절에서 문구 보강

## 5. 사과나무잎 `appleleaf` — 시든 잎 주의 추가 (등급 C·확실성 C 유지)

**원문 열람:** https://www.thetortoisetable.org.uk/plant-database/viewplants/?plant=23. 2026-10-15 사본과 문구가 같다.
- "Apple (Tree)", *Malus domestica*, Feed Sparingly.
- "The pips/seeds from the apple contain cyanide and should be avoided. The leaves, as they get older and wilt, produce a cyanic compound, so although your tortoise will come to no harm if he accidentally nibbles a few fallen leaves, it is wise to prevent him from doing so if possible."

**문제:** 복숭아나무잎 `peachleaf`(원문 plant=615)는 같은 주의를 한계와 판정 설명에 담았다. 사과나무잎에는 이 주의가 빠져 있었다.

**추가한 한계 1줄** (`data/public_assessments.json`, 영어는 `data/i18n/en/strings_en.json`):
- **한국어:** "원문은 사과나무 잎이 오래되어 시들면 시안 화합물이 생긴다고 설명한다. 떨어진 잎 몇 장을 우연히 뜯어 먹어도 해는 없지만 가능하면 먹지 못하게 하라고 권하므로, 오래되거나 시든 잎·떨어진 잎은 급여하지 않음"
- **영어:** "The source explains that apple leaves produce a cyanic compound as they get older and wilt. It says a few fallen leaves nibbled by accident do no harm but advises preventing this where possible, so older, wilted or fallen leaves are not fed"

**원칙:**
- 원문이 구분한 두 상황(우연한 소량은 해 없음, 가능하면 막을 것)을 그대로 옮겼다.
- 독성 용량이나 중독 주장은 덧붙이지 않았다.
- 씨앗 주의는 이 잎 기록의 범위 밖이다. 열매·씨앗과 잎의 판정을 섞지 않는다는 한계가 이미 있다.

**결정 기록:** `data/appleleaf_wilted_leaf_caution_20261016.json` (수정 전·후 값, 원문 인용)
