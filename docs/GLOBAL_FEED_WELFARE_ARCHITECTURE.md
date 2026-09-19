# Global Feed Welfare Evidence Architecture v1

## Goal
거북밥 DB를 단순한 '먹여도 되는 식물 목록'이 아니라, 육지거북 먹이 복지(food welfare)를 위한 추적 가능한 근거 시스템으로 확장한다. 검색 유입과 판정 source truth는 분리한다.

## 핵심 차별점
1. 식물명(identity), 급여근거(feeding evidence), 영양성분(nutrition), 독성/항영양(toxicology), 이용가능성(Korea availability)을 서로 다른 근거축으로 저장한다.
2. 대상 동물 범위를 정확히 기록한다: exact T. graeca ibera > T. graeca > Mediterranean Testudo > Testudo spp. > tortoise general > herbivorous reptile.
3. 야생섭식(observed ingestion), 선호(selection/preference), 전문 사육권고(husbandry recommendation), 독성자료(toxicology)를 서로 치환하지 않는다.
4. 식물의 잎·꽃·줄기·뿌리·열매·종자와 생/건조 상태를 분리한다.
5. 모든 결론에 supports / does_not_support / limitations를 남긴다.
6. 근거가 없으면 '안전'이 아니라 '미확정'으로 표시한다.

## Evidence record 확장 필드
- source_id / source_type / citation / DOI-PMID-URL / publication_year
- animal_taxon / taxon_directness
- plant_taxon / plant_part / preparation_state
- evidence_kind: wild_ingestion | preference | captive_husbandry | clinical | toxicology | nutrition | taxonomy | occurrence
- geography / season / life_stage / sample_size
- supports
- does_not_support
- limitations
- observed_at / reviewed_at
- provenance_status

## Korea Plant Coverage
대한민국에서 접할 가능성이 있는 식물을 다음 세 층으로 관리한다.
A. 국내 자생·귀화 관속식물 master inventory
B. 국내 식품·채소·허브·사료·원예 유통식물 inventory
C. 실제 거북 먹이 질문 빈도가 높은 priority inventory

master inventory에 포함됐다는 이유로 급여 가능 판정을 만들지 않는다. 모든 항목은 identity-only / evidence-found / assessed / unresolved 상태를 가진다.

## Source hierarchy
### Taxonomy / Korea occurrence
- National Species List of Korea / NIBR
- Korea National Arboretum Checklist of Vascular Plants in Korea
- Kew Plants of the World Online
- GBIF checklist/occurrence

### Tortoise-specific
- peer-reviewed Testudo feeding ecology and nutrition literature
- veterinary reviews/manuals
- Tortoise Trust
- British Chelonia Group
- The Tortoise Table

### Nutrition
- MFDS K-FIND
- RDA Korean Food Composition Table
- USDA FoodData Central

### Toxicology / plant chemistry
독성 또는 항영양 주장은 tortoise-specific 임상/독성 근거가 있는지 먼저 확인하고, 일반 식물화학 자료만 있는 경우 Testudo 임상효과로 확대하지 않는다.

## Welfare dimensions
식물별 최종 페이지는 단순 Safe/Unsafe를 넘어 다음 축을 보여준다.
- Identity certainty
- Taxon applicability
- Feeding evidence
- Toxicology / anti-nutritional evidence
- Nutritional context
- Plant-part restrictions
- Contamination/collection risk
- Evidence gaps

## Non-negotiable interpretation rules
- wild ingestion != captive recommendation
- preference != nutritional adequacy
- Safe to Feed != staple/unlimited
- absence of toxicity report != proven safety
- genus-level evidence != species-level evidence
- related tortoise species != exact Ibera evidence
- nutrition composition != feeding safety
- Korean retail name != botanical identity

## Scale target
1단계: 현재 69종의 evidence depth 강화.
2단계: 한국에서 흔히 구매·채집·재배되는 수백 종을 priority ingest.
3단계: 대한민국 관속식물 master inventory 전체를 identity index로 확보하고, 먹이 관련성이 높은 순서대로 evidence review.
4단계: 영문 UI와 국제 식물명/동의어 검색을 추가해 해외에서도 동일한 evidence graph를 사용.

중요: '모든 식물에 판정'이 목표가 아니라 '모든 식물을 검색할 수 있고, 근거가 있는 것과 없는 것을 정확히 구분'하는 것이 목표다.
