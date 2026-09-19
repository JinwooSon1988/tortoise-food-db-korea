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


## Expansion Architecture — Reptile Nutrition Evidence Graph

거북밥 DB의 장기 데이터 모델은 특정 거북 종 또는 식물만을 전제로 하지 않는다. UI 브랜드는 단계적으로 확장하되 source truth는 처음부터 범용 파충류 먹이 evidence graph로 설계한다.

### Animal identity
- order / family / genus / species / subspecies
- life_stage / reproductive_state
- wild_or_captive_context
- feeding_ecology: herbivorous | omnivorous | insectivorous | carnivorous | opportunistic
- geographic_population when evidence is population-specific

### Feed identity
food_domain:
- plant
- fungi
- invertebrate
- vertebrate_prey
- formulated_feed
- supplement

각 food item은 taxonomic identity와 market identity를 분리한다. 식물은 plant_part와 preparation_state, 동물성 먹이는 whole/prey-part, live/frozen/dried 등 상태를 별도 필드로 둔다.

### Evidence relationship
판정의 기본 단위는 '먹이 자체'가 아니라:
ANIMAL TAXON × FOOD TAXON/ITEM × PART/STATE × EVIDENCE CONTEXT
관계다.

같은 민들레라도 Ibera와 green iguana의 근거는 별개이며, 같은 곤충이라도 종·크기·gut-loading·사육조건에 따라 근거를 분리한다.

### Welfare dimensions
향후 식물성 먹이뿐 아니라 전체 먹이에서 다음 복지축을 평가할 수 있도록 한다.
- nutritional adequacy
- dietary diversity
- fiber/structural properties
- mineral balance
- hydration contribution
- toxicology / anti-nutritional compounds
- physical feeding hazard
- contamination / pesticide / pathogen risk
- prey welfare and humane feeding considerations where relevant
- behavioral enrichment / natural foraging expression
- life-stage suitability
- evidence uncertainty

### Internationalization
canonical scientific identity를 중심으로 ko/en 및 향후 다국어 common-name layer를 분리한다. 언어가 달라도 같은 evidence record를 공유한다.

### Expansion order
Phase A — Mediterranean Testudo 식물 먹이 evidence depth
Phase B — 한국 식물 master inventory + 검색가능 identity index
Phase C — 다른 초식·잡식 파충류(육지거북, 이구아나류, 유로매스틱스류 등) 식물 evidence
Phase D — invertebrate feeder evidence
Phase E — vertebrate prey / formulated diets / supplements
Phase F — 국제 다국어 reptile nutrition evidence platform

확장은 기존 판정의 범위를 넓혀 복사하는 방식이 아니라, animal-food 관계별 근거를 추가하는 방식으로 수행한다.


## Global Plant Corpus — worldwide-first collection policy

한국 availability는 수집 범위를 제한하는 조건이 아니라 별도 metadata다. 세계 어느 지역에서든 파충류 먹이와 관련될 가능성이 있는 식물은 우선 canonical identity corpus에 수집하고, 한국에서 현재 구할 수 없다는 이유로 제외하지 않는다.

### Geographic availability layer
각 식물은 급여 판정과 독립적으로 다음 정보를 가질 수 있다.
- native_range
- introduced_range
- cultivated_regions
- common_market_regions
- korea_status: native | naturalized | cultivated | imported | specialty_only | not_confirmed
- availability_sources
- availability_observed_at

availability는 safety/evidence verdict를 올리거나 내리지 않는다.

### Global ingestion pipeline
1. 세계 식물 canonical backbone 확보
2. accepted scientific name / synonym / family / taxonomic authority 정규화
3. 국가·지역별 common names 연결
4. occurrence/cultivation/market availability 연결
5. reptile/tortoise feeding evidence 탐색
6. toxicology/anti-nutritional evidence 탐색
7. nutrition composition 연결
8. evidence conflict와 identity ambiguity 기록
9. human review를 거친 assessment 생성
10. 공개 페이지에는 evidence state와 uncertainty를 함께 표시

### Candidate source families
- global taxonomy/checklists: Kew POWO, World Flora Online, Catalogue of Life, GBIF
- regional floras and national biodiversity databases
- peer-reviewed ecology, veterinary, nutrition and toxicology literature
- specialist reptile/tortoise husbandry databases and organizations
- official food-composition/agriculture databases
- botanical garden, herbarium and invasive-species resources when identity/distribution evidence is needed

### Data asset principle
원문을 무차별 복제하는 것이 아니라, provenance가 추적되는 구조화된 사실과 근거 관계를 축적한다. 자동 수집 후보와 검증 완료 레코드는 분리하며, 중복·동의어·오동정·상충근거를 검증 엔진이 탐지하도록 한다.

장기 목표는 '한국에서 살 수 있는 식물 DB'가 아니라 전 세계 식물 corpus 위에 reptile-food evidence graph를 얹는 것이다. 한국 availability는 그 graph의 첫 지역화 layer다.
