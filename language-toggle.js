(()=>{const K='tfdblang';
const SCRIPT=document.currentScript;const ROOT=SCRIPT?new URL('.',SCRIPT.src).href:new URL('./',location.href).href;
const T={
'이 식물, 먹여도 될까?':'Can my tortoise eat this plant?',
'식물 이름만 검색하세요.':'Search for a plant by name.',
'먹여도 되는지 먼저':'See the feeding verdict first',
'보여드리고, 왜 그런지와 논문·원자료는 필요할 때 확인할 수 있습니다.':'and explore the reasoning and original research whenever you need more detail.',
'육지거북 먹이 근거 데이터베이스':'Evidence-based tortoise food database',
'근거 기반 육지거북 먹이 DB':'Evidence-based tortoise food database',
'판정 확인':'Check feeding verdict',
'정확한 이름을 몰라도 됩니다. 한글명·영문명·학명 중 하나만 입력하세요.':'Search by a common name, Korean name, or scientific name.',
'검색 결과 없음 ≠ 안전 · 아직 공개 판정을 찾지 못한 식물일 수 있습니다.':'No result does not mean safe. This plant may not yet have a published assessment.',
'급여 판정':'Feeding verdict',
'먹여도 되는지 먼저 확인':'Find out whether a plant is suitable for feeding',
'이유와 주의':'Reasons and precautions',
'급여 부위·예외·위험 구분':'Plant parts, exceptions, and potential risks',
'검증 가능한 근거':'Traceable evidence',
'원문 자료와 한계 확인':'Review original sources and their limitations',
'전체 식물 데이터':'All plant data',
'검색하지 않고도 공개된 식물을 이름·판정과 함께 한 번에 확인할 수 있습니다.':'Browse all published plants and their feeding assessments without searching.',
'전체 식물 보기':'Browse all plants',
'근거 검토 방법':'How we evaluate evidence',
'거북밥 · 근거 기반 육지거북 먹이 데이터베이스':'Tortoise Food DB · Evidence-based tortoise nutrition',
'먼저 급여 등급을 확인하고, 필요한 경우 근거·영양자료까지 비교하세요.':'Check the feeding grade first, then explore the evidence and nutrient data when needed.',
'한글명·영문명·학명 검색':'Search by common or scientific name',
'종류':'Category',
'적합성 전체':'All grades',
'종류 전체':'All categories',
'과 전체':'All families',
'영양자료 전체':'All nutrient data',
'우선 권장':'Recommended',
'조건부 급여':'Feed with conditions',
'제한 급여':'Limited feeding',
'급여 제외':'Do not feed',
'판정 보류':'Assessment pending',
'이름순':'Name (A–Z)',

'3초 결론':'3-second answer','직접근거':'Direct evidence','근거수준':'Evidence level','종별 특이사항':'Species-specific notes','아래 내용은 특정 종에서 확인된 별도 근거다. 이 내용을 다른 육지거북 종에 자동으로 적용하지 않는다.':'The following is separate evidence confirmed for a specific species. Do not automatically transfer it to other tortoise species.','별도 판정':'Separate assessment','공개 판정 없음':'No public assessment','종 특이·간접 근거':'Species-specific / indirect evidence','지중해 Testudo 근거':'Mediterranean Testudo evidence','육지거북 일반 근거':'General tortoise evidence','간접 적용 근거':'Indirectly applicable evidence','실제 급여에서는 이렇게 해석하세요':'What this means in practice','급여 역할':'Feeding role','확인된 부위·상태':'Plant part / state supported by evidence','확인되지 않은 것':'What remains unknown','이 판정은 어디까지 적용될까?':'How far does this assessment apply?',
'먹이기 전에 식물부터 확인하세요':'Identify the plant before feeding',
'왜 이런 결론이 나왔을까?':'Why did we reach this conclusion?',
'현재 근거의 한계':'Limits of the current evidence',
'이 판정으로 말할 수 없는 것':'What this assessment cannot establish',
'이 근거가 지지하는 내용':'What this evidence supports',
'이 근거만으로 말할 수 없는 내용':'What this evidence alone cannot establish','결론':'Conclusion','등급은 아래 적용 범위와 제한사항 안에서 해석한다. 급여 가능 판정도 단독 주식·무제한 급여를 뜻하지 않는다.':'Interpret the grade within the applicability and limitations below. A feedable assessment does not mean a sole staple or unlimited feeding.','⚠ 근거 충돌 또는 안전성 미해결':'⚠ Conflicting evidence or unresolved safety','야생 섭식 기록이 있지만 독성·항영양성분 또는 다른 동물의 수의학적 위험 신호도 확인됐다. 야생에서 먹는다는 사실만으로 사육 급여 안전성을 확정하지 않는다.':'Wild feeding has been recorded, but toxicity, antinutritional factors, or veterinary risk signals in other animals are also documented. Wild consumption alone does not establish captive-feeding safety.','현재 공개판정의 걸림돌:':'Current barrier to a public assessment:','야생에서 이 식물을 실제 먹이로 이용한 근거다.':'Evidence that this plant was actually consumed as food in the wild.','원자료 식물명:':'Plant name in the original source:','현재 수용명:':'Currently accepted name:','근거 ID:':'Evidence ID:','6. 야생에서는 실제로 어떻게 먹었나?':'6. How is it actually eaten in the wild?','야생 섭식 자료가 있으면 어떤 육지거북이 어디에서 어떤 방법으로 이 식물을 먹은 것이 확인됐는지 보여준다.':'When wild-feeding data are available, this section shows which tortoise consumed the plant, where, and how.','야생에서 먹었다는 사실은 중요한 근거지만, 사육장에서 마음껏 먹여도 된다는 뜻은 아니다.':'Wild consumption is important evidence, but it does not mean the plant can be fed freely in captivity.','수분':'Water','인':'Phosphorus','단백질':'Protein','영양성분 수치는 식품성분 자료이며 육지거북의 독성 한계치나 단독 급여비율을 의미하지 않는다.':'Nutrient values are food-composition data; they do not represent tortoise toxicity thresholds or sole-diet feeding ratios.','검증된 공식 영양성분 자료가 아직 연결되지 않았다.':'No verified official nutrient-composition record is linked yet.','자료 부재를 0으로 처리하거나 안전·위험 판정의 근거로 사용하지 않는다.':'Missing data are not treated as zero or used as evidence of safety or risk.','← 다른 먹이 검색':'← Search another food','아욱 주의:':'Mallow note:','한국 유통명 아욱을 Malva parviflora로 자동 매핑하지 않는다.':'The Korean market name 아욱 is not automatically mapped to Malva parviflora.','영양성분표는 식물의 영양적 맥락을 이해하기 위한 보조자료다. Ca:P, 섬유질 또는 특정 영양소 수치가 좋아도 독성·항영양성분·식물동정·대상종 근거를 대신하지 않으며, 이 수치만으로 급여 등급을 올리지 않는다.':'The nutrient table provides nutritional context only. Favorable Ca:P, fiber, or other nutrient values do not replace evidence on toxicity, antinutritional factors, plant identity, or the target taxon, and do not raise a feeding grade by themselves.','여기에는 연구자가 검토한 학술논문과 원자료를 모은다. 어려운 논문을 전부 읽지 않아도 되도록 먼저 핵심을 풀어 설명하고, 직접 확인하고 싶은 사람을 위해 DOI·PMID와 원문 연결도 함께 제공한다.':'This section gathers peer-reviewed research and original sources. Key points are explained first, with DOI, PMID, and source links for readers who want to verify the originals.','전문 사육자료와 동료심사 논문은 성격이 다르므로 같은 수준의 근거로 취급하지 않는다.':'Specialist husbandry sources and peer-reviewed papers are different evidence types and are not treated as equivalent.','같은 과·카테고리의 다른 항목으로 이동하기 위한 기능이다. 식물학적 유사성이 동일한 급여 안전성·영양가·권장도를 뜻하지 않는다.':'These links navigate to other entries in the same family or category. Botanical similarity does not imply identical feeding safety, nutritional value, or recommendation.','거북밥 DB':'Tortoise Food DB','직접 근거':'Direct evidence','전문 사육 근거':'Specialist husbandry evidence','근연 분류군 근거':'Related-taxon evidence','성분 근거':'Composition evidence','정확한 대상 분류군':'Exact target taxon','종 수준':'Species level','지중해 육지거북류(Testudo속)':'Mediterranean tortoises (genus Testudo)','초식 파충류 일반':'Herbivorous reptiles in general','분류군 수준':'Taxon level','원문 링크 미등록':'Original-source link not registered','직접 근거 포함':'Includes direct evidence','전문 사육 근거 중심':'Primarily specialist husbandry evidence','간접·맥락 근거 중심':'Primarily indirect/contextual evidence','공개 근거 미연결':'No public evidence linked','범위 미확인':'Scope unverified','대상 동물 미확인':'Target animal unverified','부위 정보 미확인':'Plant part unverified','근거가 다루는 부위':'Plant part covered by evidence','근거 수준':'Evidence level','신뢰도':'Confidence','검토중':'Under review','판정 핵심':'Assessment summary','근거 구성':'Evidence composition','근거 적용범위':'Evidence applicability','실제 적용 원칙':'Practical application rule','근거 충돌 또는 안전성 미해결':'Conflicting evidence or unresolved safety','추가 검토 필요':'Further review needed','야생 섭식 기록':'Wild feeding record','적용범위 확인 필요':'Applicability needs verification','대상 거북 미상':'Tortoise taxon unknown','지역 미상':'Location unknown','확인 방법':'Observation method','미상':'Unknown','먹은 부위':'Part consumed','시기':'Period','섭식 기록':'Feeding observation','이 기록이 뜻하는 것':'What this record shows','이 기록만으로 말할 수 없는 것':'What this record cannot establish','야생에서는 실제로 어떻게 먹었나?':'How was it actually eaten in the wild?','식이섬유':'Fiber','칼슘':'Calcium','칼륨':'Potassium','비타민 C':'Vitamin C','자료 기준:':'Data basis:','자료명:':'Dataset:','원자료:':'Original source:','검증된 영양성분 자료':'Verified nutrient data','중요:':'Important:','다른 먹이 검색':'Search another food','거북밥 · 근거 기반 판정':'Tortoise Food DB · Evidence-based assessment','더 깊이 보고 싶다면 — 학술자료와 원논문':'Go deeper — academic studies and original sources',
'대상 범위':'Scope',
'식물 분류':'Plant taxonomy',
'대상 동물':'Target animal',
'식물 부위·상태':'Plant part / state',
'연구 대상':'Study subject',
'식물·부위':'Plant / part',
'근거 직접성':'Evidence directness',
'적용 범위':'Applicability',
'이 자료가 지지하는 것:':'What this source supports:',
'이 자료만으로 말할 수 없는 것:':'What this source cannot establish:',
'원문/초록 열기':'Open source / abstract',
'근거 읽는 법':'How to read the evidence',
'해당 대상·질문을 직접 다룸':'Directly addresses the target and question',
'육지거북 사육을 전문적으로 다루는 자료':'Specialist tortoise husbandry source',
'근연·맥락 근거':'Related-taxon / contextual evidence',
'참고 가능하지만 그대로 전이할 수 없음':'Useful context, but not directly transferable',
'성분 존재를 보여줄 뿐 급여 안전성을 단독 증명하지 않음':'Shows constituent presence only; does not establish feeding safety by itself',
'아래 내용은 이 판정이 직접 증명하지 못하는 범위다. 확인되지 않은 급여량·빈도·장기 안전성을 임의로 보충하지 않는다.':'The following falls outside what this assessment directly establishes. Unverified feeding amounts, frequency, and long-term safety are not invented.',
'야생에서 먹었다는 기록 ≠ 무제한 급여 권장. 사람용 영양자료 ≠ 육지거북 독성 한계치. 근거 부족 ≠ 안전.':'Wild consumption ≠ unlimited feeding recommendation. Human nutrition data ≠ tortoise toxicity thresholds. Lack of evidence ≠ safety.',
'자료에 없는 급여량·빈도·장기 안전용량은 임의로 만들지 않는다. 야생 섭식도 단독 주식이나 무제한 급여의 뜻으로 바꾸지 않는다.':'Feeding amounts, frequency, and long-term safe doses absent from the evidence are not invented. Wild feeding observations are not converted into staple or unlimited-feeding recommendations.',
'현재 공개 가능한 개별 근거 레코드가 연결되지 않았다. 따라서 안전성을 추정하지 않는다.':'No individual evidence record is currently linked for public display, so safety is not inferred.',
'현재 이 식물에 직접 연결된 동료심사 논문 레코드는 없다. 전문 DB 근거와 학술 근거를 구분해 표시한다.':'No peer-reviewed paper record is currently linked directly to this plant. Specialist database evidence and academic evidence are shown separately.',
'육지거북에게 먹여도 되는지 현재 확인된 근거로 판정한다.':'Assesses whether this plant can be fed to tortoises using currently verified evidence.','이 판정은 어디까지 적용되나':'How far does this assessment apply?','이유·위험·원자료까지 보기 →':'See rationale, risks, and original sources →','일치하는 공개 판정을 찾지 못했습니다.':'No matching public assessment was found.','두 글자 이상 입력하면 바로 검색합니다.':'Type at least two characters to search instantly.','한글명 · 영문명 · 학명으로 검색할 수 있습니다.':'Search by Korean name, English name, or scientific name.','현재 공개 판정':'Public assessments available','다른 이름·영문명·학명으로 다시 검색해 보세요. 판정 전 후보는 검색 결과에 노출하지 않습니다.':'Try another common name, English name, or scientific name. Unreviewed candidates are not shown in search results.','이 판정은 어디까지 적용되나':'How far does this assessment apply?','🐢 거북밥 DB':'🐢 Tortoise Food DB','이거, 먹여도 될까?':'Can my tortoise eat this?','먹이 이름을 검색해 식물 정체, 급여 판정, 적용 범위와 근거를 확인한다.':'Search a food to check plant identity, feeding assessment, applicability, and supporting evidence.','먹이 검색':'Food search','종이 다르면 같은 식물도 근거 적용 범위가 달라진다. 다른 종의 판정을 자동 전이하지 않는다.':'Evidence scope can differ by species. Assessments are not automatically transferred from another taxon.','전체 식물 보기':'Browse all plants','근거 읽는 법':'How to read evidence','그리스 육지거북':'Greek tortoise','이베라 그리스 육지거북':'Ibera Greek tortoise','헤르만 육지거북':'Hermann’s tortoise','마지나타 육지거북':'Marginated tortoise','러시안 육지거북':'Russian tortoise','설카타 육지거북':'Sulcata tortoise','레오파드 육지거북':'Leopard tortoise','검색':'Search','오늘 마트에서 고르기':'Browse market foods','마트·시장에서 구하기 쉬운 등록 식물부터 확인':'Start with registered plants commonly found in shops and markets.','야생초 찾아보기':'Explore wild plants','채집 전 동정·오염·근거 범위를 함께 확인':'Check identification, contamination risk, and evidence scope before collecting.','피해야 할 먹이 확인':'Check foods to avoid','현재 DB에서 급여 제외로 판정된 항목 확인':'Review foods currently excluded from feeding in this database.','빠른 탐색은 구매·채집 권장이 아니라 현재 DB의 검색 범위를 좁히는 기능이다.':'Quick paths narrow the database search; they are not recommendations to buy or collect plants.','전체':'All','마트·시장':'Market','야생초':'Wild plants','혼합식 활용':'Mixed diet','제한·보조':'Limited / supplemental','급여 제외':'Do not feed','검색 결과는 식물 동정이나 무제한 급여 승인이 아니다. 상세 근거와 적용 범위를 함께 확인한다.':'A search result is not a plant identification or approval for unlimited feeding. Review the evidence and its applicability.','전문 데이터':'Research tools','전체 69종 DB':'Full plant database','판정·종류·과·근거등급·영양성분을 한 표에서 비교':'Compare assessments, categories, families, evidence grades, and nutrition data in one table.','근거 중심 상세 보기':'Evidence-focused guide','등록 식물의 적용 범위와 근거를 집중 확인':'Review how evidence applies to registered plants and where its limits are.','근거를 이렇게 읽는다':'How to read the evidence','직접근거':'Direct evidence','대상 종·아종에서 확인된 자료':'Evidence observed in the target species or subspecies','적용범위':'Applicability','이베라·Mediterranean Testudo·일반 육지거북 등을 구분':'Distinguishes Ibera, Mediterranean Testudo, general tortoise evidence, and other scopes','근거등급':'Evidence grade','자료의 직접성과 품질을 함께 표시':'Summarizes evidence directness and quality','한계':'Limits','야생 섭식을 사육 급여비율로 바꾸지 않는다.':'Wild feeding observations are not converted into captive feeding ratios.','전체 식물 데이터 한눈에 보기':'Browse the full plant database','등록된 전체 식물을 표로 펼쳐 보고 적합성·종류·과·근거등급·영양성분별로 정렬한다.':'Browse registered plants in one table and sort by assessment, category, family, evidence grade, and nutrition data.','전체 식물 69종 보기 →':'View all plants →','판정 원칙':'Assessment principles','야생 섭식 ≠ 무제한 급여 권장 · 사람용 영양자료 ≠ 육지거북 독성 한계치 · 영양성분 수치만으로 급여 판정을 바꾸지 않는다.':'Wild consumption ≠ unlimited feeding · Human nutrition data ≠ tortoise toxicity thresholds · Nutrient values alone do not determine a feeding assessment.','전체 식물':'All plants','핵심 먹이':'Evidence guide','지중해형 육지거북 먹이 DB':'Mediterranean-type tortoise food database','공통적인 먹이 원칙을 먼저 보여주고, 종·아종에 직접 귀속되는 근거는 상세 페이지에서 구분한다.':'Shows shared feeding principles first; species- and subspecies-specific evidence remains distinguished on detail pages.','데이터를 불러오는 중...':'Loading database…','일치하는 먹이를 찾지 못했다.':'No matching food found.','판정 보류':'Assessment pending','학명 확인 중':'Scientific name under review','현재 공개 근거와 적용 범위를 상세 페이지에서 확인한다.':'Review the currently available evidence and applicability on the detail page.','적용 범위':'Applicability','확인 중':'Under review','근거':'Evidence','상세 근거 보기 →':'View evidence →','혼합식으로 활용 가능':'Suitable for mixed feeding','제한적으로 혼합 급여':'Limited mixed feeding','가끔 보조적으로 급여':'Occasional supplemental feeding','급여하지 않음':'Do not feed','지중해 Testudo':'Mediterranean Testudo','설카타육지거북':'Sulcata tortoise','레오파드육지거북':'Leopard tortoise','레드풋육지거북':'Red-footed tortoise','옐로우풋육지거북':'Yellow-footed tortoise','엘롱가타육지거북':'Elongated tortoise','방사거북':'Radiated tortoise','인도별거북':'Indian star tortoise','버마별거북':'Burmese star tortoise','앵무부리육지거북':'Angulate tortoise','전체 식물 DB':'Full plant database','전체 식물 보기 →':'View all plants →','등록 식물':'Registered plants','근거 중심 상세 보기':'Evidence-focused details','육지거북 일반':'General tortoise','전체 식물 데이터':'All plant data','불러오는 중...':'Loading…','← 검색으로':'← Back to search','한글명·영문명·학명 검색':'Search Korean, English, or scientific name','적합성 전체':'All assessments','종류 전체':'All categories','과 전체':'All families','영양자료 전체':'All nutrition data','영양자료 있음':'Nutrition data available','영양자료 없음':'No nutrition data','열 제목을 누르면 오름차순 ↕ 내림차순으로 정렬한다. 영양성분은 확인된 공식 식품성분 자료가 있는 경우에만 표시하며, 수치 자체가 급여 적합성을 결정하지 않는다.':'Click a column heading to sort ascending or descending. Nutrient values are shown only when verified official food-composition data are available; nutrient values alone do not determine feeding suitability.','혼합식 활용 가능':'Mixed diet','제한적 혼합 급여':'Limited mixed feeding','가끔 보조 급여':'Occasional supplement','식물명':'Plant','영문명':'English name','학명':'Scientific name','과':'Family','종류':'Category','적합성':'Assessment','수분 g':'Water g','섬유 g':'Fiber g','단백질 g':'Protein g','있음':'Available','미확인':'Unverified','영양자료':'Nutrition data','← 거북밥 DB 검색으로':'← Back to Tortoise Food DB search','급여 판정':'feeding assessment','판정 해석:':'Assessment interpretation:','이 판정은 어디까지 적용되는가':'How far does this assessment apply?','식단 내 역할':'Role in the diet','식물 이름':'Plant names','학명 표기':'Scientific name','식물동정 — 이름이 같아도 같은 식물은 아니다':'Plant identification — the same name does not guarantee the same plant','근거의 한계와 해석 주의':'Evidence limits and interpretation','추가로 확인할 식물':'Related plants to review','탐색 링크:':'Discovery links:','이 판정 공유하기':'Share this assessment','링크 복사':'Copy link','링크 복사 완료':'Link copied','다른 먹이 찾기 →':'Find another food →','아직 공개 권장 역할을 확정하지 않음':'No public dietary role has been established yet','종별 판정 근거 검토 미완료':'Taxon-specific evidence review is incomplete','근거 부족 상태에서는 안전하다고 추정하지 않는다.':'Do not assume safety when evidence is insufficient.','단독·무제한 급여 판정으로 해석하지 않는다.':'Do not interpret this as approval for exclusive or unlimited feeding.'};
const ko=new Map(Object.entries(T)), en=new Map(Object.entries(T).map(([a,b])=>[b,a]));
const ph={ko:'예: 민들레, 질경이, 치커리, 무청',en:'e.g. dandelion, plantain, chicory'};
function swapText(root,map){const w=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);let n;while(n=w.nextNode()){const raw=n.nodeValue,trim=raw.trim();if(!trim)continue;if(map.has(trim))n.nodeValue=raw.replace(trim,map.get(trim));else if(document.documentElement.lang==='en'){if(/^현재 등록된 \d+종을 검색한다\.$/.test(trim)){const m=trim.match(/\d+/)[0];n.nodeValue=raw.replace(trim,`Search ${m} registered plants.`)}else if(/^전체 식물 \d+종 보기 →$/.test(trim)){n.nodeValue=raw.replace(trim,'View all plants →')}}}}
function toggleEvidence(lang){document.querySelectorAll('.ko-evidence').forEach(x=>x.hidden=lang==='en');document.querySelectorAll('.en-evidence').forEach(x=>x.hidden=lang!=='en')}
function apply(lang){document.documentElement.lang=lang;try{localStorage.setItem(K,lang)}catch(e){};const map=lang==='en'?ko:en;swapText(document.body,map);const brand=document.querySelector('.brand span');if(brand)brand.textContent=lang==='en'?'Tortoise Food DB':'거북밥';const title=document.querySelector('title');if(title)title.textContent=lang==='en'?'Can my tortoise eat this plant? | Tortoise Food DB':'이 식물, 먹여도 될까? | 거북밥';const input=document.getElementById('searchInput');if(input)input.placeholder=ph[lang];const count=document.getElementById('catalogCount');if(count){const m=count.textContent.match(/(\d+)/);if(m)count.textContent=lang==='en'?'Public assessments available: '+m[1]+' plants':'현재 공개 판정 '+m[1]+'종을 검색할 수 있습니다.'}toggleEvidence(lang);document.querySelectorAll('[data-lang]').forEach(b=>{b.setAttribute('aria-pressed',String(b.dataset.lang===lang));b.classList.toggle('active',b.dataset.lang===lang)});window.dispatchEvent(new CustomEvent('tfdblanguagechange',{detail:{lang}}))}
function navLabel(lang){return lang==='en'?{home:'Home',back:'Back'}:{home:'홈',back:'뒤로'}}
function ensureNav(){const path=new URL(location.href).pathname.replace(/\/index\.html$/,'/');const rootPath=new URL(ROOT).pathname;if(path===rootPath||document.querySelector('.detailnav')){document.querySelectorAll('.utilitynav').forEach(n=>n.remove());return}if(document.querySelector('.utilitynav'))return;const n=document.createElement('nav');n.className='utilitynav';n.setAttribute('aria-label','Page navigation');n.innerHTML='<a class="utilityhome" href="'+ROOT+'">⌂ <span>홈</span></a><button class="utilityback" type="button">← <span>뒤로</span></button>';document.body.prepend(n);n.querySelector('.utilityback').onclick=()=>{if(history.length>1)history.back();else location.href=ROOT}}
function updateNav(lang){const l=navLabel(lang),n=document.querySelector('.utilitynav');if(!n)return;n.querySelector('.utilityhome span').textContent=l.home;n.querySelector('.utilityback span').textContent=l.back}
/* One page, one search engine: language switching updates the current DOM without navigation. */
function boot(){
 ensureNav();
 let lang='ko';
 try{lang=localStorage.getItem(K)==='en'?'en':'ko'}catch(e){}const requested=new URLSearchParams(location.search).get('lang');if(requested==='ko'||requested==='en')lang=requested;
 // Legacy plant detail pages have a separately authored full English page.
 // Route there rather than mixing translated labels with untranslated Korean paragraphs.
 const detailMatch=location.pathname.match(/^(.*\/tortoise-food-db-korea\/)plant\/([^/]+)\/?(?:index\.html)?$/);
 const methodMatch=location.pathname.match(/^(.*\/tortoise-food-db-korea\/)guides\/research-method\/?(?:index\.html)?$/);
 if(detailMatch&&lang==='en'){
   try{localStorage.setItem(K,'en')}catch(e){}
   location.replace(detailMatch[1]+'en/plant/'+detailMatch[2]+'/?lang=en'+location.hash);
   return;
 }
 if(methodMatch&&lang==='en'){
   try{localStorage.setItem(K,'en')}catch(e){}
   location.replace(methodMatch[1]+'en/guides/research-method/?lang=en'+location.hash);
   return;
 }
 const host=document.querySelector('.topmeta');
 if(host){
   const nav=document.createElement('nav');
   nav.className='langswitch';
   nav.setAttribute('aria-label','언어 / Language');
   nav.innerHTML='<button type="button" data-lang="ko" aria-pressed="true">한국어</button><button type="button" data-lang="en" aria-pressed="false">English</button>';
   if(!host.querySelector('.langswitch'))host.prepend(nav);
 }
 const activeNav=document.querySelector('.langswitch');
 if(activeNav){
   activeNav.addEventListener('click',e=>{
     const btn=e.target.closest('button[data-lang]');
     if(!btn)return;
     const next=btn.dataset.lang;
     if(next!==document.documentElement.lang){const url=new URL(location.href);url.searchParams.set('lang',next);try{history.replaceState(history.state,'',url.pathname+url.search+url.hash)}catch(e){}apply(next);updateNav(next)}
   });
 }
 apply(lang);
 updateNav(lang);
 // Keep the user's explicit choice across all internal pages and browser navigation.
 // Normalize links immediately as well: keyboard navigation and newly opened tabs
 // should preserve the selected language, not only mouse clicks.
 function syncInternalLinks(){
   document.querySelectorAll('a[href]').forEach(link=>{
     if(link.hasAttribute('download')||link.getAttribute('href').startsWith('#'))return;
     let target;try{target=new URL(link.href,location.href)}catch(_){return}
     if(target.origin!==location.origin||!target.pathname.startsWith(new URL(ROOT).pathname))return;
     const base=new URL(ROOT).pathname;
     const relative=target.pathname.slice(base.length);
     if(document.documentElement.lang==='en' && (/^guides\/research-method\/?$/.test(relative)||/^plant\/[^/]+\/?$/.test(relative))){
       target.pathname=base+'en/'+relative.replace(/\/$/,'')+'/';
     }else if(document.documentElement.lang==='ko' && (/^en\/guides\/research-method\/?$/.test(relative)||/^en\/plant\/[^/]+\/?$/.test(relative))){
       target.pathname=base+relative.replace(/^en\//,'').replace(/\/$/,'')+'/';
     }
     target.searchParams.set('lang',document.documentElement.lang);
     if(target.href!==link.href)link.href=target.href;
   });
 }
 syncInternalLinks();
 // Back/forward cache may restore a DOM in the language used before navigation.
 // Reconcile it with the current persisted choice when the page becomes visible.
 window.addEventListener('pageshow',event=>{
   if(!event.persisted)return;
   let preferred=document.documentElement.lang;
   try{preferred=localStorage.getItem(K)==='en'?'en':'ko'}catch(_){}
   const explicit=new URLSearchParams(location.search).get('lang');
   if(explicit==='en'||explicit==='ko')preferred=explicit;
   if(preferred!==document.documentElement.lang){apply(preferred);updateNav(preferred)}
   syncInternalLinks();
 });
 window.addEventListener('tfdblanguagechange',syncInternalLinks);
 document.addEventListener('click',e=>{
   const link=e.target.closest('a[href]');
   if(!link||link.hasAttribute('download')||link.target==='_blank')return;
   let target;try{target=new URL(link.href,location.href)}catch(_){return}
   if(target.origin!==location.origin||!target.pathname.startsWith(new URL(ROOT).pathname))return;
   if(target.searchParams.get('lang')!==document.documentElement.lang){
     target.searchParams.set('lang',document.documentElement.lang);
     link.href=target.href;
   }
 },true);
}
document.addEventListener('DOMContentLoaded',boot)})();