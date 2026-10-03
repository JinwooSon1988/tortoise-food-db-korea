from pathlib import Path
import json, html, re, sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from public_verdict import load_assessments, representative, display, species_notes, scope_label, by_plant, public_plants

ROOT=Path(__file__).resolve().parents[1]
SITE_URL="https://jinwooson1988.github.io/tortoise-food-db-korea"
all_plants=json.loads((ROOT/"data/plants.json").read_text(encoding="utf-8"))

# Public rendering uses the same canonical assessment registry and the same
# representative-verdict rule as the home search (verdict-core.js).
assessments=load_assessments()
assessments_by_plant=by_plant(assessments)
retail=json.loads((ROOT/"data/korean_retail_name_map.json").read_text(encoding="utf-8"))
evidence_records=json.loads((ROOT/"data/public_evidence_records.json").read_text(encoding="utf-8")).get("records",[])
evidence_by_id={e["id"]:e for e in evidence_records}
nutrition_records=json.loads((ROOT/"data/plant_nutrition_v56.json").read_text(encoding="utf-8")).get("plants",[])
nutrition_by_id={n["plant_id"]:n for n in nutrition_records if n.get("verification_status")=="verified"}
wild_records=json.loads((ROOT/"data/wild_feeding_evidence.json").read_text(encoding="utf-8")).get("records",[])
wild_by_plant={}
for w in wild_records:
    wild_by_plant.setdefault(w.get("plant_id"),[]).append(w)
risk_records=json.loads((ROOT/"data/wild_candidate_risk_screening.json").read_text(encoding="utf-8")).get("records",[])
risk_by_plant={r.get("plant_id"):r for r in risk_records}
ibera=json.loads((ROOT/"data/ibera_direct_feeding_evidence_v56.json").read_text(encoding="utf-8"))
ibera_sources={s["source_id"]:s for s in ibera.get("sources",[])}
ibera_by_plant={}
for o in ibera.get("observations",[]):
    if o.get("plant_id"): ibera_by_plant.setdefault(o["plant_id"],[]).append(o)
images=json.loads((ROOT/"data/verified_plant_images_v56.json").read_text(encoding="utf-8")).get("images",[])
image_by_plant={i["plant_id"]:i for i in images if i.get("identity_scope") in {"exact_species","exact_subspecies","exact_variety"}}
curated_identity=json.loads((ROOT/"data/curated_identity_notes.json").read_text(encoding="utf-8")).get("notes",{})

# Public detail pages: the same set the home search exposes (non-candidate + any public assessment).
plants=public_plants(all_plants,assessments)
retail_by_id={r["plant_id"]:r for r in retail}
directness_ko={"direct":"직접 근거","expert_husbandry":"전문 사육 근거","related_taxon":"근연 분류군 근거","contextual":"맥락 근거","composition_only":"성분 근거"}
applicability_ko={"exact_taxon":"정확한 대상 분류군","species":"종 수준","mediterranean_testudo":"지중해 육지거북류(Testudo속)","tortoise_general":"육지거북 일반","herbivorous_reptile_general":"초식 파충류 일반","composition_only":"성분 자료","taxon_group":"분류군 수준"}

def esc(v): return html.escape(str(v or ""),quote=True)
def rich(v):
    """Escape, then render *text* as italic (used for scientific names in curated notes)."""
    return re.sub(r"\*([^*]+)\*",r"<i>\1</i>",esc(v))

def source_kind(e):
    t=str(e.get("source_type") or "")
    if t.startswith("peer_reviewed") or e.get("pmid"): return (0,"동료심사 논문")
    if t.startswith("academic") or t=="conference_proceedings": return (1,"학술 연구")
    if t.startswith("veterinary") or "veterinary" in t: return (2,"수의학 자료")
    if t.startswith("specialist") or t.startswith("expert"): return (3,"전문 사육·식물 자료")
    if "taxonomy" in t or "taxonomic" in t or "botanical" in t or "biodiversity" in t or "agriculture" in t: return (4,"식물동정·분류 자료")
    if "nutrition" in t or "food_composition" in t: return (5,"성분 참고자료")
    if t.startswith("regulatory_"): return (6,"공식 평가자료")
    return (7,"기타 공공·맥락 자료")

def animal_taxon_display(value):
    v=str(value or "").strip()
    exact={
        "Mediterranean Testudo":"지중해 Testudo 육지거북",
        "Mediterranean tortoises":"지중해 육지거북",
        "Tortoise general":"육지거북 일반",
        "Tortoises":"육지거북",
        "Herbivorous reptiles":"초식 파충류",
        "Plant-eating reptiles":"초식 파충류",
        "Reptiles":"파충류",
        "Animals general":"동물 일반",
        "General context":"일반 맥락 자료",
        "Not an animal feeding study":"동물 급여시험이 아님",
        "Not applicable":"해당 없음",
        "not_applicable":"해당 없음",
        "Centrochelys sulcata":"설카타육지거북 (Centrochelys sulcata)",
        "Chersina angulata":"앵귤레이트육지거북 (Chersina angulata)",
        "Testudo graeca":"그리스육지거북 (Testudo graeca)",
        "Testudo graeca graeca":"그리스육지거북 T. g. graeca",
        "Testudo graeca ibera":"이베라그리스육지거북 (T. g. ibera)",
        "Testudo hermanni":"헤르만육지거북 (Testudo hermanni)",
        "Testudo hermanni hermanni":"서부헤르만육지거북 (T. h. hermanni)",
        "Testudo spp.":"Testudo속 육지거북",
        "Testudo graeca ibera and eastern Testudo graeca clades":"이베라그리스육지거북 및 동부 Testudo graeca 계통",
        "Testudo graeca, T. hermanni, T. marginata, T. horsfieldii":"그리스·헤르만·마지나타·러시안육지거북",
        "Herbivorous tortoises, with Mediterranean observations":"초식 육지거북 일반 및 지중해 육지거북 관찰",
        "Bos taurus (cattle)":"소 (Bos taurus) — 육지거북 급여시험 아님",
        "Mus musculus / Rattus norvegicus (toxicology context)":"생쥐·랫드 독성 맥락 — 육지거북 급여시험 아님",
        "Chinese hamster ovary cells; in vitro":"중국햄스터 난소세포 시험관 연구 — 동물 급여시험 아님",
        "HaCaT cell line; not an animal feeding study":"HaCaT 세포주 연구 — 동물 급여시험 아님",
        "Cats and plant chemistry":"고양이 및 식물화학 맥락 — 육지거북 급여시험 아님",
        "Plant chemistry; mammalian experimental context":"식물화학·포유류 실험 맥락 — 육지거북 급여시험 아님",
        "primarily mammalian/medicinal toxicology; not tortoise feeding":"주로 포유류·약용 독성학 자료 — 육지거북 급여시험 아님",
    }
    shown=exact.get(v,v)
    if shown==v and re.search(r"[A-Za-z]{3,}", v) and not re.search(r"[가-힣]", v):
        # Scientific taxon strings are expected here; prose-like metadata is not.
        if re.search(r"\b(study|context|feeding|toxicology|general|animals|reptiles|observations|chemistry)\b", v, re.I):
            return "원자료에 명시된 대상 동물 범위 — 육지거북 직접 급여시험 여부는 근거 역할·적용 한계에서 별도 확인"
    return shown

def plant_taxon_display(value):
    v=str(value or "").strip()
    exact={
        "Taraxacum / Sonchus / Trifolium / Medicago taxa reported in the study":"연구에서 보고된 Taraxacum·Sonchus·Trifolium·Medicago 분류군",
        "Cichorium, Taraxacum, Medicago, Potentilla and Sedum taxa reported":"보고된 Cichorium·Taraxacum·Medicago·Potentilla·Sedum 분류군",
        "See linked plant concept(s); source scope preserved from evidence registry":"연결된 식물 항목 — 출처의 적용 범위를 그대로 유지",
        "Cucurbita moschata within the source's squash scope":"출처의 squash 범위에 포함되는 Cucurbita moschata",
        "Perilla spp.; Korean food concept Perilla frutescens":"Perilla spp. — 국내 식품 범위는 Perilla frutescens",
        "Grasses as a broad dietary/context category; exact grass taxa require separate evidence":"넓은 식단 맥락의 벼과 식물 — 개별 종은 별도 근거 확인 필요",
        "Mustard greens category; assessment master Brassica juncea requires identity confirmation":"갓류 범위 — Brassica juncea 종 동정 확인 필요",
    }
    shown=exact.get(v,v)
    if shown==v and re.search(r"[A-Za-z]{3,}", v) and not re.search(r"[가-힣]", v):
        # Keep bare scientific names, but never expose English scope prose in Korean mode.
        if re.search(r"\b(source|scope|study|reported|context|concept|category|assessment|warning|identity|mapped|requires|listed)\b", v, re.I):
            return "원자료에 명시된 식물 분류군 범위 — 세부 종 동정과 적용 범위는 원자료 기준"
    return shown

def part_state_display(value):
    v=str(value or "").strip()
    exact={
        "leaves":"잎",
        "young leaves":"어린잎",
        "young leaves; Fabaceae flowers/inflorescences also reported":"어린잎 — 콩과 꽃·꽃차례 섭식도 함께 보고됨",
        "young leaves; flowers/inflorescences also reported with leaves":"어린잎 — 잎과 함께 꽃·꽃차례 섭식도 보고됨",
        "not resolved in extracted source text":"원문 추출본에서 섭식 부위가 확인되지 않음",
        "fruit":"열매",
        "grass":"풀",
        "leafy greens":"잎채소",
        "leafy vegetable":"잎채소",
        "young leaves":"어린 잎",
        "young fresh leaves":"어린 생잎",
        "flowers and leaves":"꽃과 잎",
        "leaves and flowers":"잎과 꽃",
        "identity only":"식물 동정만 확인",
        "taxonomic identity only":"분류학적 동정만 확인",
        "whole taxon identity":"분류군 동정만 확인",
        "sprouted shoots":"발아한 새싹",
        "wild diet":"야생 섭식 기록",
        "plant material":"식물체",
        "leaves and flowers; root explicitly excluded":"잎과 꽃 — 뿌리는 이 근거의 대상이 아님",
        "leaves and flowers; root explicitly distinguished":"잎과 꽃 — 뿌리는 별도 부위로 구분됨",
        "flowers and leaves; roots/tubers excluded":"꽃과 잎 — 뿌리·덩이뿌리는 대상에서 제외",
        "leaves and flowers; fruit not inferred":"잎과 꽃 — 열매까지 같은 근거로 일반화하지 않음",
        "herb; seeds explicitly excluded":"초본 식물체 — 씨앗은 명시적으로 제외",
        "leaves only; cob/kernel excluded":"잎만 해당 — 속대·낟알은 제외",
        "carrot tops distinguished from root":"당근 지상부 — 뿌리와 구분",
        "leaves and tuber distinguished":"잎과 덩이뿌리를 구분",
        "grass vegetation; not grain/seed equivalence":"풀의 영양생장부 — 곡물·씨앗과 동일시하지 않음",
        "young grasses; mature seeds explicitly distinguished":"어린 풀 — 성숙한 씨앗과 구분",
        "young grass; dried hay; dry seed heads distinguished":"어린 풀·건초·마른 씨앗이삭을 각각 구분",
        "wild plant material; exact consumed part not established in this record":"야생 식물체 — 실제 섭식 부위는 이 기록에서 확정되지 않음",
        "wild plant material; non-quantitative observations":"야생 식물체 — 정량 급여자료가 아닌 관찰 기록",
        "leaves / flowers":"잎·꽃",
        "leaves / aerial material":"잎·지상부",
        "leaves / plant material":"잎·식물체",
        "leaves / new growth":"잎·새순",
        "leaves / flowers / berries as stated by source":"출처에 명시된 잎·꽃·열매",
        "leaves, flowers and stems":"잎·꽃·줄기",
        "leaves, fresh":"생잎",
        "new leaf growth and flowers":"새잎·꽃",
        "primarily young leaves":"주로 어린 잎",
        "young aerial shoots; seed/other parts not silently substituted":"어린 지상부 새순 — 씨앗·다른 부위로 대체 해석하지 않음",
        "aerial culinary herb":"식용 허브의 지상부",
        "aerial culinary plant":"식용 식물의 지상부",
        "aerial herb material":"초본의 지상부",
        "whole culinary plant / aerial material":"식용 식물 전체·지상부",
        "whole plant / feeding plant entry":"식물 전체 — 급여 식물 항목",
        "plant; exact part not specified in entry":"식물체 — 해당 출처에서 정확한 부위는 특정하지 않음",
        "plant; source entry does not establish a part-specific tortoise dose":"식물체 — 특정 부위의 육지거북 급여량을 확정하는 자료가 아님",
        "plant material; exact part varies by observation":"식물체 — 관찰마다 실제 부위가 다름",
        "fruit; leaves and flowers separately noted":"열매 — 잎·꽃은 별도로 구분됨",
        "fruit concept; species mapping explicitly limited":"열매 범위 — 종 수준 적용은 명시된 범위로 제한",
        "leaves, unripe fruit and ripe fruit distinguished":"잎·미숙 열매·성숙 열매를 각각 구분",
        "green leaves and roots":"녹색 잎·뿌리",
        "leaves and root; plant-level toxicology":"잎·뿌리 — 식물 수준 독성학 자료",
        "rhizome/root preparations and extracts":"뿌리줄기·뿌리 제제 및 추출물",
        "whole plant, especially bulb":"식물 전체 — 특히 구근",
        "whole plant; leaves and seeds specifically discussed":"식물 전체 — 잎·씨앗을 별도로 언급",
        "pads and fruit":"패드형 줄기·열매",
        "sprouted shoots":"발아 새싹",
        "young plant material; exact part varies by observation":"어린 식물체 — 관찰마다 실제 부위가 다름",
        "mature aerial plant material":"성숙한 지상부 식물체",
        "feeding-trial plant material; flowering/seed stage discussed":"급여시험 식물체 — 개화·결실 단계를 구분해 언급",


        "3-day-old sprouts versus mature broccoli":"3일령 새싹과 성숙 브로콜리를 구분",
        "As described by the source; do not generalize beyond the cited note":"출처에 기술된 범위만 해당 — 인용된 설명 밖으로 일반화하지 않음",
        "As specified in the source; composition/toxicology findings must not be generalized across untested plant parts or animal taxa.":"출처에 명시된 성분·독성학 범위만 해당 — 시험하지 않은 식물 부위나 동물 분류군으로 일반화하지 않음",
        "Leaves, flowers, shoots and selected dried plant materials; item-specific details in source":"잎·꽃·새순 및 일부 건조 식물체 — 항목별 세부 범위는 원자료에 따름",
        "aerial growth sampled at full senescence; species-specific phytochemical analysis":"완전 노화 단계의 지상부 — 해당 종의 식물화학 분석",
        "aerial parts; steam-distilled essential oil":"지상부의 수증기 증류 정유 — 일반 식물체 급여와 동일시하지 않음",
        "aerial plant material":"지상부 식물체",
        "aerial plant material; exact listed mint taxa only":"지상부 식물체 — 명시된 민트 분류군에만 해당",
        "broccoli plant; flower head and flowers described":"브로콜리 식물체 — 꽃봉오리 머리와 꽃을 구분해 기술",
        "broccoli plant; sprouting broccoli entry, not a quantified microgreen trial":"브로콜리 식물체 — 발아 브로콜리 항목이며 정량 마이크로그린 급여시험은 아님",
        "five genotypes/varieties; chemotype-dependent composition":"5개 유전형·품종 — 화학형에 따라 성분이 달라질 수 있음",
        "flowers, unripe fruit, leaves / wild fresh plant":"꽃·미숙 열매·잎 — 야생 생식물체",
        "fresh whole plant and extracts; toxicology literature summarized":"신선한 전초와 추출물 — 독성학 문헌 요약이며 일반 급여시험과 동일시하지 않음",
        "genus-level hazard warning; not an Oenanthe javanica feeding trial":"속 수준 위해 경고 — 미나리(Oenanthe javanica) 급여시험이 아님",
        "herb; flowers also described":"초본 식물체 — 꽃도 별도로 기술",
        "identity only; Korean crop name 근대":"식물 동정만 확인 — 국내 작물명 ‘근대’",
        "leaf food concept; pyrethrin-rich Chrysanthemum taxa excluded":"잎 식품 범위 — 피레트린 함량이 높은 Chrysanthemum 분류군은 제외",
        "leaf scope used by this food concept":"해당 식품 개념에서 사용하는 잎 범위",
        "leaf/tree sap context; fruit separately distinguished":"잎·수액 맥락 — 열매는 별도로 구분",
        "leafy/aerial plant material":"잎·지상부 식물체",
        "leaves / aerial plant material":"잎·지상부 식물체",
        "leaves and cauliflower head":"잎과 콜리플라워 꽃머리",
        "leaves and stems identified in faecal diet analysis":"분변 식이 분석에서 확인된 잎과 줄기",
        "leaves; multiple Morus taxa/varieties":"잎 — 여러 Morus 분류군·품종 자료",
        "methanolic leaf extract":"잎의 메탄올 추출물 — 생잎 급여와 동일시하지 않음",
        "plant material/new untreated growth":"식물체·처리하지 않은 새 생장부",
        "plant material; cultivar-specific quantity not established":"식물체 — 품종별 정량 범위는 확정되지 않음",
        "plant material; older leaves specifically discussed":"식물체 — 오래된 잎을 별도로 논의",
        "plant material; species identification required":"식물체 — 종 수준 동정 필요",
        "plant; Pelargonium distinguished from hardy Geranium":"식물체 — Pelargonium과 내한성 Geranium을 구분",
        "plant; Tagetes distinguished from Calendula":"식물체 — Tagetes와 Calendula를 구분",
        "plant; culinary herb":"식용 허브 식물체",
        "plant; cultivar/chemotype variation separately evidenced":"식물체 — 품종·화학형 차이는 별도 근거로 구분",
        "plant; genus-level source scope":"식물체 — 출처의 적용 범위는 속 수준",
        "species-level use record":"종 수준 이용 기록",
        "tree leaves / plant material":"나무 잎·식물체",
        "tree plant material; leaf concept mapped conservatively":"나무 식물체 — 잎 범위는 보수적으로 연결",
        "young leaves and flowers":"어린 잎과 꽃",
        "As specified in the cited source and evidence note; plant parts must not be silently generalized.":"인용 자료에 명시된 부위·상태만 해당 — 다른 부위로 임의 일반화하지 않음",
        "Part/state distinctions are preserved in the source note; do not generalize across roots, leaves, flowers, fruits or seeds.":"출처의 부위·상태 구분을 유지 — 뿌리·잎·꽃·열매·씨앗 사이를 일반화하지 않음",
    }
    shown=exact.get(v,v)
    if shown==v and re.search(r"[A-Za-z]{3,}", v) and not re.search(r"[가-힣]", v):
        return "출처에 명시된 식물 부위·상태만 해당 — 다른 부위나 상태로 임의 일반화하지 않음"
    return shown

def evidence_support_display(value):
    v=str(value or "").strip()
    mixed_ko={
        "The assessment records the Korean crop identity 근대 as Beta vulgaris subsp. cicla, linking the domestic food concept to the chard taxonomic scope.":"평가 기록은 국내 작물명 ‘근대’를 Beta vulgaris subsp. cicla로 확인하여 국내 식품 개념을 근대(chard)의 분류학적 범위와 연결한다.",
    }
    if v in mixed_ko:
        return mixed_ko[v]
    # Korean canonical evidence sentences must pass through unchanged.
    # Otherwise the English verdict-token fallback below can corrupt Korean particles
    # (for example "급여하지 않음으로" -> "급여하지 않음로").
    if re.search(r"[가-힣]", v):
        return v
    exact={
        "Safe to Feed":"출처는 급여 가능하다고 분류한다.",
        "Safe to Feed as part of a varied diet":"출처는 다양한 식단의 일부로 급여 가능하다고 분류한다.",
        "Safe to Feed as part of a wider varied diet":"출처는 폭넓고 다양한 식단의 일부로 급여 가능하다고 분류한다.",
        "Feed in Moderation":"출처는 제한 급여로 분류한다.",
        "Do not Feed":"출처는 급여하지 않음으로 분류한다.",
        "Safe to Feed; succulent, feed in moderation":"출처는 급여 가능하다고 분류하지만, 다육식물이므로 과량 급여하지 않도록 제한한다.",
        "Safe to Feed; succulent, feed in moderation to avoid loose stools":"출처는 급여 가능하다고 분류하지만, 다육식물이므로 묽은 변을 피하기 위해 과량 급여하지 않도록 제한한다.",
        "Safe to Feed; source warns not to confuse with toxic Aruncus dioicus":"출처는 급여 가능하다고 분류하며, 독성이 있는 Aruncus dioicus와 혼동하지 말라고 경고한다.",
        "Feed in Moderation; source notes high saponins":"출처는 제한 급여로 분류하며 사포닌 함량이 높다고 언급한다.",
        "Feed in Moderation; Brassicaceae/goitrogen context":"출처는 제한 급여로 분류하며 십자화과·갑상선종 유발물질 맥락을 함께 제시한다.",
        "Do not Feed; regarded as unsuitable food for tortoises":"출처는 육지거북 먹이로 부적합하다고 보아 급여하지 않음으로 분류한다.",
        "Do not Feed; pyrrolizidine alkaloid concern and potential liver damage":"출처는 피롤리지딘 알칼로이드와 잠재적 간 손상 우려를 들어 급여하지 않음으로 분류한다.",
        "Analytical evidence that common buckwheat leaves contain phototoxic fagopyrins.":"분석 자료에서 메밀 잎에 광독성을 일으킬 수 있는 파고피린(fagopyrin)이 존재함을 확인했다.",
        "Wild T. g. ibera were documented consuming plant taxa including Taraxacum, Sonchus, Trifolium and Medicago.":"야생 이베라그리스육지거북(T. g. ibera)이 Taraxacum·Sonchus·Trifolium·Medicago 분류군의 식물을 섭식한 기록이 있다. 이는 야생 섭식 관찰이며 사육 환경의 급여량·빈도를 뜻하지 않는다.",
        "Documents wild Ibera feeding observations involving the listed plant genera.":"자료에는 야생 이베라그리스육지거북이 해당 식물 속을 섭식한 관찰 기록이 있다. 정량 급여시험은 아니다.",
        "In a cattle feeding study, 3 of 5 calves developed atypical interstitial pneumonia; emphysema and pulmonary edema were reported. Flowering/seed-stage material was described as more toxic and associated with higher perilla ketone.":"소 급여시험에서 송아지 5마리 중 3마리에게 비정형 간질성 폐렴이 발생했고 폐기종과 폐부종이 보고됐다. 개화·결실 단계 식물체는 독성이 더 높은 것으로 기술됐으며 페릴라 케톤 함량 증가와 연관됐다. 포유류 독성시험 결과이므로 육지거북의 독성 용량으로 직접 환산할 수 없다.",
        "GC/MS analysis detected perilla ketone in two of five P. frutescens genotypes, demonstrating meaningful genotype/chemotype variation.":"GC/MS 분석에서 P. frutescens 5개 유전형 중 2개에서 페릴라 케톤이 검출돼 유전형·화학형에 따른 유의미한 성분 차이가 확인됐다.",
        "Reports nutritional/feed-quality differences among mulberry taxa/varieties, supporting the need to preserve species/variety identity rather than assigning one fixed composition to generic 'mulberry leaf'.":"뽕나무 분류군·품종 사이의 영양 및 사료 품질 차이가 보고됐다. 따라서 ‘뽕잎’ 전체에 하나의 고정 성분값을 적용하지 말고 종·품종 정체성을 구분해야 한다.",
        "Species-specific review reports mouse acute testing of fresh O. javanica at 15 g/kg without mortality or evident acute organ toxicity, while high-dose dry powder increased sperm deformity and reduced body weight/food consumption; high-dose phenolic extract produced reversible subchronic toxicity in rats.":"미나리(O. javanica) 해당 종을 대상으로 한 문헌고찰에서 생식물 15 g/kg을 사용한 생쥐 급성시험에서는 사망이나 뚜렷한 급성 장기독성이 관찰되지 않았다. 반면 고용량 건조분말에서는 정자 기형 증가와 체중·섭취량 감소가, 고용량 페놀성 추출물에서는 흰쥐의 가역적 아급성 독성이 보고됐다. 이는 포유류 시험으로 육지거북 급여 안전성을 직접 입증하지 않는다.",
        "Long-term specialist husbandry practice supports a varied, high-fiber Testudo diet centered on appropriate weeds and leafy plants; the source specifically lists plantain, sow thistle, mallow, dandelion, red clover and several supplemental greens/dried leaves.":"장기간의 전문 사육 경험 자료는 적절한 야생초와 잎 식물을 중심으로 한 다양하고 고섬유질인 Testudo 식단을 지지한다. 질경이·방가지똥류·아욱류·민들레·붉은토끼풀과 여러 보조 잎채소·건조 잎을 구체적으로 제시한다.",
        "Cynodon dactylon leaves and stems were identified as important food items in wild Testudo graeca diet.":"야생 Testudo graeca의 식이 분석에서 우산잔디(Cynodon dactylon)의 잎과 줄기가 주요 섭식 항목으로 확인됐다. 야생 섭식 자료이며 사육 급여 비율을 직접 정하는 자료는 아니다.",
        "Cynodon dactylon was a principal food item across three of four seasons at one study site.":"한 조사 지역에서 우산잔디(Cynodon dactylon)는 네 계절 중 세 계절에 주요 섭식 항목으로 확인됐다. 해당 지역의 야생 관찰 결과로 사육 환경의 정해진 급여 빈도나 비율을 의미하지 않는다.",
        "Wild Testudo graeca graeca were documented consuming the taxon reported as Medicago hispida, now treated here as Medicago polymorpha.":"야생 Testudo graeca graeca가 당시 Medicago hispida로 보고된 분류군을 섭식한 기록이 있으며, 여기서는 현재 분류에 따라 Medicago polymorpha로 다룬다. 야생 섭식 관찰이지 정량 급여시험은 아니다.",
        "Species-specific phytochemical evidence documents saponin-class constituents in Medicago polymorpha and supports retaining an antinutritional caution.":"Medicago polymorpha의 해당 종의 식물화학 자료에서 사포닌 계열 성분이 확인돼 항영양성분에 대한 주의를 유지할 근거가 된다. 성분이 검출됐다는 사실만으로 육지거북에서 어느 양부터 독성이 나타나는지 알 수는 없다.",
        "Three-day-old broccoli sprouts had much higher glucoraphanin-related glucosinolate levels than mature broccoli in the studied cultivars.":"조사된 품종에서 3일령 브로콜리 새싹은 성숙 브로콜리보다 글루코라파닌 관련 글루코시놀레이트 함량이 훨씬 높았다. 이는 성분분석 결과이며 육지거북 급여 안전성을 직접 시험한 자료는 아니다.",
        "The veterinary toxicology database classifies Althaea officinalis as a non-poisonous plant and notes no animal poisoning cases in the cited literature.":"수의독성학 데이터베이스는 Althaea officinalis를 비독성 식물로 분류하고 인용 문헌에서 동물 중독 사례가 없다고 설명한다. 다만 이는 Testudo의 적정 급여량·빈도를 확정하는 급여시험은 아니다.",
        "Under the tested in-vitro conditions, the leaf extract did not induce genotoxic effects and contained proanthocyanidins, flavonols and triterpenoid saponins.":"시험관 내 조건에서 잎 추출물은 유전독성 효과를 유발하지 않았고 프로안토시아니딘·플라보놀·트리테르페노이드 사포닌이 확인됐다. 추출물 기반 시험관 연구이므로 생잎의 육지거북 급여 안전성과 동일시하지 않는다.",
        "A. deliciosa green leaves contained little to no bioactive iridoids in the reported analysis, while roots contained higher levels.":"보고된 분석에서 A. deliciosa의 녹색 잎에는 생리활성 이리도이드가 거의 없거나 매우 적었고 뿌리에는 더 높은 수준이 확인됐다. 식물 부위별 성분분석 결과이며 육지거북 급여시험은 아니다.",
        "Provides a species-specific concentrated-essential-oil hazard signal and documents biologically active volatile constituents.":"해당 종의 농축 정유에서 위해 가능성을 시사하는 신호와 생리활성 휘발성 성분이 보고됐다. 농축 정유 자료를 일반 식물체의 육지거북 급여와 동일시하지 않는다.",
        "Provides toxicology and pharmacology context for medicinal rhizome/root preparations.":"약용 뿌리줄기·뿌리 제제에 관한 독성학·약리학적 맥락을 제공한다. 약용 제제 자료는 일반 식물체의 육지거북 급여시험이 아니다.",
        "Do not Feed; specialist tortoise guidance advises avoiding this high-protein legume.":"육지거북 전문 사육 지침은 단백질 함량이 높은 이 콩과 식물을 피하도록 하며 급여하지 않음으로 분류한다.",
        "Feed in Moderation; brassica/goitrogen concern and varied-diet limits apply.":"출처는 제한 급여로 분류하며 배추과·갑상선종 유발물질 우려와 다양한 식단 내 제한을 적용한다.",
        "Leaves and flowers may be nibbled but should be fed sparingly.":"출처는 잎과 꽃을 먹을 수는 있으나 소량으로 드물게 급여해야 한다고 설명한다.",
        "Young leaves may be fed in moderation.":"출처는 어린 잎을 제한적으로 급여할 수 있다고 설명한다.",
        "Classifies Hollyhock as Safe to Feed and states flowers and leaves can be fed as part of a wider varied diet.":"접시꽃(Hollyhock)을 급여 가능하다고 분류하며 꽃과 잎을 폭넓고 다양한 식단의 일부로 급여할 수 있다고 설명한다.",
        "Classifies Lemon Balm as Feed in Moderation and recommends it only as part of a wider varied diet.":"레몬밤을 제한 급여로 분류하며 폭넓고 다양한 식단의 일부로만 사용하도록 권고한다.",
        "Classifies German Chamomile as Feed Sparingly and advises against regular offering.":"저먼 캐모마일을 소량·드물게 급여로 분류하며 정기적인 급여는 피하도록 권고한다.",
        "Classifies Achillea millefolium as Do not Feed and advises avoiding planned feeding.":"서양톱풀(Achillea millefolium)을 급여하지 않음으로 분류하며 계획적인 급여를 피하도록 권고한다.",
        "Classifies Portulaca oleracea as Do not Feed and cites high oxalic-acid content as its reason for avoiding planned feeding.":"쇠비름(Portulaca oleracea)을 급여하지 않음으로 분류하며 높은 옥살산 함량을 계획 급여를 피하는 이유로 제시한다.",
        "Classifies Bellis perennis as Do not Feed while noting an incidental nibble is not expected to cause harm.":"Bellis perennis를 급여하지 않음으로 분류하지만 우발적으로 조금 뜯어 먹은 경우까지 해를 일으킬 것으로 보지는 않는다고 설명한다.",
        "Classifies oregano (Origanum vulgare) as Safe to Feed within a varied tortoise diet.":"오레가노(Origanum vulgare)를 다양한 육지거북 식단 안에서 급여 가능하다고 분류한다.",
        "Classifies culinary sage (Salvia officinalis) as Feed in Moderation.":"식용 세이지(Salvia officinalis)를 제한 급여로 분류한다.",
        "Classifies thyme (Thymus spp.) as Safe to Feed as part of a wider varied diet.":"타임(Thymus spp.)을 폭넓고 다양한 식단의 일부로 급여 가능하다고 분류한다.",
        "Feed in Moderation; the entry permits it as a small part of a wider varied diet while flagging goitrogen concerns.":"폭넓고 다양한 식단의 작은 일부로 제한 급여할 수 있으나 갑상선종 유발물질 우려를 함께 제시한다.",
        "Feed in Moderation. The fruit is described as mostly water and useful for hydration or hiding medication; leaves and flowers may be fed in small amounts.":"열매는 대부분 수분으로 구성돼 수분 보충이나 약을 숨겨 먹이는 용도로 활용할 수 있다고 설명한다. 잎과 꽃은 소량 급여할 수 있으며 전체적으로 제한 급여 범위다.",
        "Feed in Moderation. The source states it is not toxic but flags Brassicaceae goitrogen concerns when fed in quantity.":"독성 식물로 설명하지는 않지만 배추과 식물을 다량 급여할 때의 갑상선종 유발물질 우려를 제시하며 제한 급여로 분류한다.",
        "Feed in Moderation. The source permits leaves and flowers in moderation while explicitly saying never to feed the root.":"잎과 꽃은 제한적으로 급여할 수 있지만 뿌리는 절대 급여하지 말라고 명시한다.",
        "Feed Sparingly. The assessment preserves the specialist source's high-oxalate caution, occasional-use framing and hydration caution.":"전문 출처의 높은 옥살산염 주의, 가끔만 사용하는 급여 원칙과 수분 관련 주의를 보존해 소량·드물게 급여로 평가한다.",
        "Safe to Feed. Used as general-tortoise evidence for inclusion within a varied diet, not as a quantified staple prescription.":"일반 육지거북 자료에서 다양한 식단에 포함할 수 있는 급여 가능 근거로 사용한다. 정량적인 주식 비율을 정하는 자료는 아니다.",
        "Safe to Feed applies to leaves in the assessment evidence; it must not be transferred to cob, kernels or whole corn.":"급여 가능 판정은 잎에 적용되는 근거다. 옥수수 속대·알곡이나 식물 전체에 같은 판정을 그대로 적용하면 안 된다.",
        "Feed in Moderation. The assessment applies this conservatively to sunflower leaf as a small rotational supplement.":"해바라기 잎을 순환식 식단의 작은 보조 구성으로만 보수적으로 제한 급여한다.",
        "Leaves are treated as small/sparing supplementary material in the assessment; the conclusion is not extended to fruit.":"잎은 소량의 보조 식재료로만 평가하며 이 결론을 열매까지 확대하지 않는다.",
        "Feed Sparingly. The assessment limits this to small amounts of young leaves/flowers and does not extend the conclusion to fruit.":"어린 잎과 꽃을 소량·드물게 급여하는 범위로 제한하며 이 결론을 열매까지 확대하지 않는다.",
        "Feed Sparingly. The assessment uses the source's Cucurbita moschata-inclusive squash scope only as general-tortoise evidence for rare supplementary use.":"출처가 Cucurbita moschata를 포함해 다룬 호박류 범위를 일반 육지거북의 드문 보조 급여 근거로만 사용해 소량·드물게 급여로 평가한다.",
        "Do not Feed in the specialist database; the assessment therefore excludes planned feeding while explicitly not treating this as an Ibera-specific toxicity trial.":"전문 DB가 급여하지 않음으로 분류하므로 계획적인 급여에서 제외한다. 다만 이를 이베라그리스육지거북에 한정된 독성시험 결과로 해석하지 않는다.",
        "The existing assessment preserves the specialist database's moderation framing for most Chrysanthemum-group plants while explicitly excluding pyrethrin-rich taxa.":"대부분의 Chrysanthemum 계열 식물에 대한 전문 DB의 제한 급여 원칙을 유지하되 피레트린 함량이 높은 분류군은 명시적으로 제외한다.",
        "The assessment preserves the specialist database's do-not-feed recommendation for fig-tree material because of irritating sap exposure.":"무화과나무 식물체는 자극성 수액 노출 우려 때문에 전문 DB의 급여하지 않음 권고를 유지한다.",
        "The existing assessment preserves the specialist database's Do not Feed category for Artemisia spp. and therefore excludes planned feeding of the Korean Artemisia princeps concept.":"전문 DB의 Artemisia spp. 급여하지 않음 분류를 유지해 국내 쑥(Artemisia princeps) 개념도 계획 급여에서 제외한다.",
        "The specialist database categorizes Pisum sativum/pea shoots as Do not Feed while also stating that the plant is not actually toxic; its rationale discusses protein, phytate and possible calcium-absorption concerns.":"전문 DB는 완두(Pisum sativum) 새순을 급여하지 않음으로 분류하지만 식물 자체가 독성이라고 하지는 않는다. 단백질·피테이트와 잠재적인 칼슘 흡수 저해 우려를 근거로 제시한다.",
        "Feed in Moderation in the specialist database; the assessment therefore keeps Pelargonium only as a small component of a varied diet.":"전문 DB의 제한 급여 분류에 따라 Pelargonium은 다양한 식단의 작은 구성으로만 사용한다.",
        "The specialist database categorizes Perilla as Do not Feed. The assessment combines that husbandry caution with separately stored mammalian toxicology and chemotype evidence while excluding planned feeding.":"전문 DB는 들깨속(Perilla)을 급여하지 않음으로 분류한다. 이 사육상 주의와 별도로 저장된 포유류 독성·화학형 근거를 함께 고려해 계획 급여에서 제외한다.",
        "Classifies kale as Feed in Moderation and permits it as part of a varied tortoise diet while flagging goitrogen concerns.":"케일을 제한 급여로 분류하며 다양한 육지거북 식단의 일부로 허용하되 갑상선종 유발물질 우려를 함께 제시한다.",
        "Classifies Taraxacum officinale as Feed in Moderation and suitable as part of a wider varied diet; notes oxalates and mild diuretic properties.":"서양민들레(Taraxacum officinale)를 제한 급여로 분류하며 폭넓고 다양한 식단에 사용할 수 있다고 설명한다. 옥살산염과 약한 이뇨 특성도 언급한다.",
        "Classifies Calendula as Safe to Feed and states flowers and leaves may be included as part of a varied diet.":"Calendula를 급여 가능하다고 분류하며 꽃과 잎을 다양한 식단의 일부로 사용할 수 있다고 설명한다.",
        "Allows young raspberry leaves and flowers sparingly as part of a varied diet.":"어린 라즈베리 잎과 꽃을 다양한 식단의 일부로 소량·드물게 급여할 수 있다고 설명한다.",
        "Allows young strawberry leaves within a varied diet.":"어린 딸기 잎을 다양한 식단의 일부로 사용할 수 있다고 설명한다.",
        "Classifies grape hyacinth (Muscari spp.) as Do not Feed and advises against growing it in tortoise enclosures.":"무스카리(Muscari spp.)를 급여하지 않음으로 분류하며 육지거북 사육장 안에서 재배하지 말라고 권고한다.",
        "Classifies grape vine leaves as Feed in Moderation and specifically permits young fresh leaves in moderation.":"포도나무 잎을 제한 급여로 분류하며 특히 어린 생잎을 제한적으로 급여할 수 있다고 명시한다.",
        "Classifies Hibiscus (Rose of Sharon) as Safe to Feed and discusses both flowers and leaves.":"무궁화(Hibiscus)를 급여 가능하다고 분류하며 꽃과 잎을 모두 다룬다.",
        "Classifies the entry as Safe to Feed and states that mulberry leaves may be used as part of a wider varied diet.":"뽕잎을 급여 가능하다고 분류하며 폭넓고 다양한 식단의 일부로 사용할 수 있다고 설명한다.",
        "Classifies Timothy Grass as Safe to Feed. It states that grazing tortoises may eat it in an enclosure and that dried Timothy hay can be used for grazing tortoises in winter.":"티머시풀을 급여 가능하다고 분류한다. 방사형 사육장에서 육지거북이 뜯어 먹을 수 있고 겨울에는 건조 티머시 건초를 활용할 수 있다고 설명한다.",
        "Classifies this Cat Grass group as Safe to Feed and states that the young grasses can be fed to tortoises.":"해당 캣그라스 그룹을 급여 가능하다고 분류하며 어린 풀을 육지거북에게 급여할 수 있다고 설명한다.",
        "Classifies Opuntia as Safe to Feed and includes both pads and fruit; it also notes that large quantities may have a laxative effect.":"Opuntia를 급여 가능하다고 분류하며 패드형 줄기와 열매를 모두 포함한다. 다량 섭취하면 완하 작용이 나타날 수 있다고도 설명한다.",
        "Classifies Sweet Potato as Do not Feed. It distinguishes the starchy tuber from the leaves and states that the leaves are not toxic as such but are not recommended because of an unfavorable calcium-to-phosphorus ratio.":"고구마를 급여하지 않음으로 분류한다. 전분질 덩이뿌리와 잎을 구분하며, 잎 자체를 독성이라고 하지는 않지만 불리한 칼슘:인 비율을 이유로 권장하지 않는다.",
        "Feed in Moderation; the entry states basil may be fed in moderation, while its strong aroma/taste may reduce palatability.":"바질은 제한 급여할 수 있으나 강한 향과 맛 때문에 기호성이 낮을 수 있다고 설명한다.",
        "Feed Sparingly; leaves are described as non-toxic but high in oxalic acid, so only small, occasional quantities are advised. The root is explicitly excluded.":"잎은 독성 식물로 설명되지는 않지만 옥살산 함량이 높아 소량을 가끔만 급여하도록 한다. 뿌리는 명시적으로 제외한다.",
        "Do not Feed; the entry cites goitrogen concerns and states broccoli is not actually toxic but is not recommended for tortoises.":"갑상선종 유발물질 우려를 들어 급여하지 않음으로 분류한다. 브로콜리를 독성 식물이라고 하지는 않지만 육지거북에게 권장하지 않는다고 설명한다.",
        "Feed Sparingly; carrot tops are described as high in oxalic acid, potassium and protein and therefore suitable only sparingly, if at all.":"당근 지상부는 옥살산·칼륨·단백질 함량이 높다고 설명하며, 급여하더라도 소량·드물게만 주도록 한다.",
        "Do not Feed; the entry explicitly says its advice applies to leaves as well as the cauliflower head and cites goitrogen concerns.":"콜리플라워 꽃머리뿐 아니라 잎에도 같은 주의가 적용된다고 명시하며 갑상선종 유발물질 우려로 급여하지 않음으로 분류한다.",
        "Do not Feed; the entry says celery is not toxic as such but is not recommended, discussing leaf oxalates, seed diuretic properties, sodium/carbohydrate content and Ca:P.":"셀러리를 독성 식물이라고 하지는 않지만 권장하지 않으며 급여하지 않음으로 분류한다. 잎의 옥살산염, 씨앗의 이뇨 특성, 나트륨·탄수화물 함량과 칼슘:인 비율을 함께 논의한다.",
        "Feed in Moderation; the entry describes coriander as a useful addition but notes oxalic acid and emphasizes use only within a larger varied diet.":"고수는 식단에 활용할 수 있지만 옥살산을 고려해 제한 급여하며, 반드시 더 폭넓고 다양한 식단의 일부로만 사용하도록 설명한다.",
        "Feed in Moderation; the entry reports no known hazards but says evidence of suitability is insufficient for broader use and explicitly says not to feed the seeds.":"알려진 위해는 없다고 설명하지만 광범위한 사용을 뒷받침할 적합성 근거가 충분하지 않아 제한 급여로 다룬다. 씨앗은 급여하지 말라고 명시한다.",
        "Do not Feed. The source distinguishes toxic leaves/unripe fruit from ripe fruit, which it still does not recommend because of its nutritional profile; it notes ripe tomato may occasionally be used to administer medication.":"급여하지 않음으로 분류한다. 독성이 문제되는 잎·미숙 열매와 성숙 열매를 구분하지만, 성숙 토마토도 영양 구성을 이유로 권장하지 않는다. 다만 약을 먹이기 위한 용도로 가끔 사용할 수 있다고 언급한다.",
        "Safe to Feed. The source describes Calendula officinalis leaves and flowers as suitable tortoise food.":"금잔화(Calendula officinalis)의 잎과 꽃을 육지거북에게 적합한 먹이로 설명하며 급여 가능하다고 분류한다.",
        "Safe to Feed. The source permits pansy leaves and flowers and distinguishes them from unrelated plants sharing similar common names.":"팬지의 잎과 꽃을 급여할 수 있다고 설명하며, 비슷한 일반명을 가진 다른 식물과 구분해야 한다고 명시한다.",
        "Safe to Feed. The source describes true Viola species as suitable tortoise food while emphasizing correct identification.":"진정한 Viola속 식물을 육지거북에게 적합한 먹이로 설명하며 급여 가능하다고 분류한다. 정확한 식물 동정을 강조한다.",
        "Feed in Moderation. The source distinguishes Tagetes marigolds from Calendula and recommends only moderate use.":"Tagetes 메리골드를 Calendula와 구분하며 제한 급여만 권장한다.",
        "Most Chrysanthemum species may be fed in moderate or small quantities as part of a varied diet.":"출처는 대부분의 Chrysanthemum 종을 다양한 식단의 일부로 제한적이거나 소량 급여할 수 있다고 설명한다. 다만 종별 차이를 무시해 모든 국화류에 일괄 적용하면 안 된다.",
        "Fescue grasses are listed as safe to feed; tall fescue endophyte concerns from ruminants are discussed separately.":"출처는 페스큐류 풀을 급여할 수 있는 먹이로 제시한다. 다만 톨페스큐의 내생균 관련 우려는 반추동물 자료로 별도 논의되며 육지거북 독성 용량으로 직접 환산하지 않는다.",
        "Specialist tortoise guidance advises not feeding broccoli because of goitrogen concerns.":"육지거북 전문 사육 지침은 갑상선종 유발물질 우려를 근거로 브로콜리를 계획적으로 급여하지 않도록 권고한다.",
        "Brassica rapa is described as acceptable as a small part of a varied tortoise diet, with goitrogen-related caution.":"출처는 Brassica rapa를 다양한 육지거북 식단의 작은 일부로 사용할 수 있다고 설명하면서 갑상선종 유발물질 관련 주의를 함께 제시한다.",
        "Mallow (Malva spp.) is listed as safe to feed and is included on a Mediterranean tortoise suitable-plant list.":"아욱류(Malva spp.)는 급여 가능한 식물로 분류되며 지중해 육지거북에 적합한 식물 목록에도 포함된다.",
        "Poa pratensis is an accepted species and is documented as used as animal food.":"Poa pratensis는 인정되는 종이며 동물 먹이로 이용된 기록이 있다. 이는 식물 정체성·이용 기록이지 육지거북 급여 안전성을 직접 입증하는 시험은 아니다.",
        "Kew recognizes Poa pratensis as an accepted species and records animal-food use.":"Kew는 Poa pratensis를 인정되는 종으로 등재하고 동물 먹이 이용 기록을 제시한다. 이는 분류·이용 근거이며 육지거북의 적정 급여량을 정하는 근거는 아니다.",
        "Specialist tortoise husbandry guidance classifies this plant as Do not Feed and notes irritant properties and poor palatability.":"육지거북 전문 사육 지침은 이 식물을 급여하지 않음으로 분류하고 자극성 및 낮은 기호성을 언급한다.",
        "Feed in Moderation; no evidence of toxicity cited, but Solanaceae context warrants caution and varied-diet use":"출처는 제한 급여로 분류한다. 독성 근거가 제시된 것은 아니지만 가지과라는 맥락을 고려해 주의하며 다양한 식단의 일부로만 사용한다.",
        "Feed in Moderation for flowers and leaves; never feed roots or tubers":"출처는 꽃과 잎을 제한 급여로 분류하지만 뿌리와 덩이뿌리는 절대 급여하지 말라고 명시한다.",
        "Feed in Moderation as part of a varied diet; florist/garden-centre pesticide-treatment caution":"출처는 다양한 식단의 일부로 제한 급여할 수 있다고 설명하며 꽃집·원예점 식물의 농약 처리 가능성을 경고한다.",
        "Safe to Feed flowers and leaves as part of a varied diet":"출처는 꽃과 잎을 다양한 식단의 일부로 급여 가능하다고 분류한다.",
        "Safe to Feed as part of a varied diet; distinguish from Citrus bergamia":"출처는 다양한 식단의 일부로 급여 가능하다고 분류하며 Citrus bergamia와 혼동하지 않도록 구분한다.",
        "Feed in Moderation; mature plants within a varied diet":"출처는 성숙한 식물체를 다양한 식단의 일부로 제한 급여하도록 분류한다.",
        "Safe to Feed; source warns not to confuse with toxic Aruncus dioicus":"출처는 급여 가능하다고 분류하지만 독성이 있는 Aruncus dioicus와 혼동하지 말라고 경고한다.",
        "The specialist plant database classifies Mallow (Malva spp.) as Safe to Feed and explicitly describes both flowers and leaves as eaten by tortoises.":"전문 식물 DB는 아욱류(Malva spp.)를 급여 가능하다고 분류하며 육지거북이 꽃과 잎을 모두 먹는다고 명시한다.",
        "The specialist database classifies the listed garden mint, spearmint and apple mint taxa as Safe to Feed / harmless if nibbled.":"전문 DB는 명시된 가든민트·스피어민트·애플민트 분류군을 급여 가능 또는 조금 뜯어 먹어도 해가 없는 것으로 분류한다.",
        "The specialist source explicitly warns that water dropworts of the genus Oenanthe are different from Filipendula dropwort and describes Oenanthe water dropworts as highly toxic plants that should be avoided.":"전문 출처는 Oenanthe속 미나리류가 Filipendula의 dropwort와 다른 식물임을 명확히 경고하며, Oenanthe 미나리류를 피해야 할 고독성 식물로 설명한다.",
        "The veterinary guidance includes mustard greens among examples used in varied diets for herbivorous reptiles; the assessment therefore treats it only as general supplementary context.":"수의학 지침은 초식 파충류의 다양한 식단 예시에 겨자잎을 포함한다. 따라서 이 자료는 일반적인 보조 맥락으로만 사용하며 Testudo에 한정된 급여량을 정하는 근거는 아니다.",
        "Provides Mediterranean Testudo husbandry context in which grasses occur within a broader fibrous plant diet. Exact grass-food conclusions are supported separately by taxon-specific specialist records.":"지중해 Testudo 사육에서 풀이 폭넓은 고섬유질 식물 식단의 일부로 사용되는 맥락을 제공한다. 개별 풀의 급여 판정은 해당 분류군을 직접 다룬 별도 전문 근거로 판단한다.",
    }
    exact.update({
        "Does not establish a Testudo graeca ibera-specific feeding percentage or fixed frequency. Dry seed heads are not equivalent to the grass or hay; the source advises removing them because they may cause eye or mouth injury.":"이 자료는 이베라그리스육지거북에 한정된 급여 비율이나 정해진 급여 빈도를 정하는 근거는 아니다. 마른 씨앗 이삭은 풀이나 건초와 동일하게 볼 수 없으며, 눈이나 입에 상처를 낼 수 있어 제거하도록 권고한다.",
        "Does not establish a Testudo graeca ibera-specific intake percentage or prove every cultivar/endophyte state equivalent.":"이 자료는 이베라그리스육지거북에 한정된 섭취 비율을 확정하지 않으며, 모든 품종과 내생균 상태를 똑같이 볼 근거는 아니다.",
        "Does not establish a Testudo graeca ibera-specific percentage, fixed frequency or unlimited use. The source itself cautions against overfeeding because of the possible laxative effect.":"이 자료는 이베라그리스육지거북에 한정된 급여 비율·정해진 급여 빈도·무제한 급여를 허용하는 근거는 아니다. 출처 자체도 완하 작용 가능성 때문에 과량 급여를 경고한다.",
        "Does not establish a Testudo graeca ibera-specific percentage, fixed frequency, essential-oil safety, or unlimited intake.":"이 자료는 이베라그리스육지거북에 한정된 급여 비율·구체적인 급여 빈도·정유의 안전성이나 무제한 섭취 허용 범위를 정하는 근거는 아니다.",
        "Does not establish a Testudo graeca ibera-specific toxic dose or prove identical hazard magnitude for every Muscari species and plant part.":"이 자료만으로 이베라그리스육지거북에서 어느 양부터 독성이 나타나는지 알 수 없으며, 모든 Muscari 종과 식물 부위의 위해 정도가 동일하다고 증명하지 않는다.",
        "Does not establish a staple percentage, unlimited feeding, Mediterranean Testudo-specific dose, or safety of similarly named Hypericum species.":"이 자료는 주식으로 사용할 비율·무제한 급여·지중해 Testudo에 한정된 급여량 또는 이름이 비슷한 다른 Hypericum 종까지 안전하다고 볼 근거는 아니다.",
        "Does not establish a toxic dose, clinical toxicity, safe captive feeding percentage, or Testudo-specific adverse effect.":"이 자료는 어느 양부터 독성이 나타나는지, 실제 임상 독성이 발생하는지, 안전한 사육 급여 비율이 얼마인지 또는 Testudo에서 어떤 이상반응이 나타나는지를 이 자료만으로 판단할 수 없다.",
        "Does not establish an Ibera-specific percentage or frequency and must not be transferred to true Geranium species merely because both may be called geranium.":"이 자료는 이베라그리스육지거북에 한정된 급여 비율이나 빈도를 정하는 근거는 아니다. 둘 다 제라늄으로 불릴 수 있다는 이유만으로 진짜 Geranium 속 식물에 판정을 옮겨 적용하면 안 된다.",
        "Does not establish captive diet percentage, feeding frequency, unlimited use, or a direct Testudo graeca ibera safety dose.":"이 자료는 사육 식단 비율·급여 빈도·무제한 급여 또는 이베라그리스육지거북에 대한 안전한 섭취량을 정하는 근거는 아니다.",
        "Does not establish captive diet percentages, feeding frequency, unlimited use, or equivalence between every species in those genera.":"이 자료는 사육 식단 비율·급여 빈도·무제한 급여 또는 해당 속에 속한 모든 종이 똑같이 안전하다고 볼 근거는 아니다.",
    })
    if v in exact:
        return exact[v]
    if v=="Does not establish a Testudo graeca ibera-specific feeding percentage or fixed frequency. Dry seed heads are not equivalent to the grass or hay; the source advises removing them because they may cause eye or mouth injury.":
        return "이베라그리스육지거북의 구체적인 식단 비율이나 급여 빈도를 정하는 자료는 아니다. 마른 씨앗 이삭은 풀이나 건초와 동일하지 않으며 눈·입을 다칠 수 있어 제거하라고 출처가 권고한다."
    if v=="Does not establish a Testudo graeca ibera-specific diet percentage, fixed frequency or unlimited use. Mature seeds are not equivalent to young grass; the source says not to allow tortoises to eat the seeds because they are too high in protein.":
        return "이베라그리스육지거북의 식단 비율·정해진 급여 빈도·무제한 급여를 정하는 자료는 아니다. 성숙한 씨앗은 어린 풀과 동일하지 않으며 단백질이 너무 높아 씨앗을 먹지 못하게 하라고 출처가 설명한다."
    if v=="Does not establish a Testudo graeca ibera-specific percentage, fixed frequency or unlimited use. The source itself cautions against overfeeding because of the possible laxative effect.":
        return "이베라그리스육지거북의 식단 비율·정해진 급여 빈도·무제한 급여를 정하는 자료는 아니다. 출처 자체도 잠재적인 완하 작용 때문에 과량 급여를 경고한다."
    if v=="Does not demonstrate direct toxicity of sweet-potato leaves in Testudo graeca ibera, nor does it justify treating accidental nibbling as poisoning. It does not establish equivalence between leaves and tuber.":
        return "고구마 잎이 이베라그리스육지거북에 직접 독성을 보인다는 자료가 아니며 우발적으로 조금 뜯어 먹은 것을 중독으로 간주할 근거도 아니다. 잎과 덩이뿌리를 동일하게 취급할 수도 없다."
    if v=="Cattle toxicity cannot be converted into a Testudo graeca ibera toxic dose, safe dose, feeding frequency or percentage. It also does not establish that every edible Korean perilla cultivar has the same perilla-ketone concentration.":
        return "소에서 확인된 독성을 이베라그리스육지거북의 독성이 나타나는 양·안전한 섭취량·급여 빈도·식단 비율로 환산할 수 없다. 또한 국내 식용 들깨의 모든 품종이 동일한 페릴라 케톤 농도를 가진다는 뜻도 아니다."
    if v=="This plant-chemistry study is not a tortoise feeding trial. It does not establish a Testudo graeca ibera toxic threshold, safe intake, frequency, or that all edible perilla cultivars contain equivalent perilla-ketone concentrations.":
        return "이 식물화학 연구는 육지거북 급여시험이 아니다. 이베라그리스육지거북의 독성 임계값·안전 섭취량·급여 빈도를 정할 수 없으며 모든 식용 들깨 품종의 페릴라 케톤 농도가 같다고 볼 수도 없다."
    if v=="This is not a Testudo graeca ibera feeding-safety study and does not establish tortoise-specific safety, dose, frequency, percentage, or a single composition value for unidentified Korean-market mulberry leaves.":
        return "이베라그리스육지거북 급여 안전성 연구가 아니므로 육지거북에서의 안전성·안전한 섭취량·급여 빈도·식단 비율을 이 자료만으로 정할 수 없다. 종·품종이 확인되지 않은 국내 유통 뽕잎에 하나의 고정 성분값을 적용할 수도 없다."
    if v=="This is not an exact-taxon Testudo graeca ibera trial. Historical-name linkage must not be used to transfer the conclusion to Chrysanthemum cinerariifolium, C. coccineum or unrelated taxa.":
        return "정확한 분류군을 대상으로 한 이베라그리스육지거북 시험이 아니다. 과거 학명 연결만으로 이 결론을 Chrysanthemum cinerariifolium·C. coccineum 또는 무관한 분류군에 그대로 적용하면 안 된다."
    if v=="This is genus-level evidence, not an Artemisia princeps-specific Testudo trial. It does not establish identical chemistry across Artemisia species or a tortoise toxic dose.":
        return "속 수준의 근거이며 Artemisia princeps를 직접 대상으로 한 Testudo 시험이 아니다. Artemisia 각 종의 화학 조성이 동일하다고 볼 수 없고 육지거북 독성 용량도 정할 수 없다."
    if v=="Does not establish an Ibera-specific percentage or frequency and must not be transferred to true Geranium species merely because both may be called geranium.":
        return "이베라그리스육지거북에 한정된 식단 비율이나 급여 빈도를 정하는 자료가 아니다. 일반명이 모두 geranium으로 불릴 수 있다는 이유만으로 진정한 Geranium속 식물에 판정을 그대로 적용하면 안 된다."
    if v=="This specialist verdict is not a Testudo graeca ibera toxicity trial. It does not establish a tortoise toxic dose, identical susceptibility to mammals, or identical perilla-ketone content across edible cultivars.":
        return "이 전문 판정은 이베라그리스육지거북 독성시험이 아니다. 육지거북 독성 용량, 포유류와 동일한 감수성 또는 식용 품종 전체의 동일한 페릴라 케톤 함량을 입증하지 않는다."
    if v=="The conclusion must not be expanded to Mentha spp. as a whole. The same source separately excludes peppermint (Mentha × piperita) and pennyroyal (Mentha pulegium); therefore a generic Korean '민트' product requires species identification before a feeding conclusion.":
        return "이 결론을 Mentha속 전체로 확대하면 안 된다. 같은 출처는 페퍼민트(Mentha × piperita)와 페니로열(Mentha pulegium)을 별도로 제외하므로 국내에서 단순히 ‘민트’로 유통되는 식물은 종을 확인한 뒤 급여 판정을 내려야 한다."
    if v=="This is a genus-level caution, not an Oenanthe javanica-specific Testudo graeca ibera toxicity study or dose-response experiment. It does not establish a tortoise toxic dose for Korean minari.":
        return "속 수준의 주의 근거이며 Oenanthe javanica를 직접 대상으로 한 이베라그리스육지거북 독성시험이나 용량-반응 시험이 아니다. 국내 미나리의 육지거북 독성 용량을 정하는 자료도 아니다."
    if v=="Does not establish safety for Testudo graeca ibera, a tortoise feeding dose or frequency, or justify transferring toxicity of other Oenanthe species to O. javanica. It also does not prove that O. javanica is safe as a captive tortoise food.":
        return "이베라그리스육지거북의 안전성·급여량·빈도를 확정하지 않으며 다른 Oenanthe 종의 독성을 O. javanica에 그대로 전이할 근거도 아니다. 반대로 O. javanica가 사육 육지거북에게 안전한 먹이라는 사실을 입증하는 자료도 아니다."
    if v=="This specialist plant-database entry is not a controlled Testudo graeca ibera feeding or toxicity trial. Common-name similarity must not be used to transfer the verdict to a different genus or species, and the category does not define an exact captive percentage, fixed frequency or unlimited use.":
        return "이 전문 식물 DB 항목은 통제된 이베라그리스육지거북 급여·독성시험이 아니다. 일반명이 비슷하다는 이유로 다른 속·종에 판정을 그대로 적용하면 안 되며, 해당 분류는 정확한 사육 식단 비율·정해진 급여 빈도·무제한 급여를 정하지 않는다."
    if v=="Does not establish captive diet percentages, feeding frequency, unlimited use, or equivalence between every species in those genera.":
        return "사육 환경의 식단 비율·급여 빈도·무제한 급여를 정하는 자료가 아니며, 해당 속의 모든 종을 똑같이 볼 수 있다는 뜻도 아니다."
    if v=="Non-quantitative observations do not establish captive diet ratios, feeding frequency, or species-level equivalence for Korean plants within the same genus.":
        return "비정량 관찰 자료이므로 사육 식단 비율·급여 빈도를 정할 수 없고, 같은 속에 속한다는 이유만으로 국내 식물 종들을 똑같이 취급할 수도 없다."
    if v=="Wild consumption does not establish unlimited captive feeding, a precise ration, or equivalence for every Testudo graeca population.":
        return "야생 섭식 관찰은 사육 환경의 무제한 급여나 정확한 배합 비율을 정하지 않으며 모든 Testudo graeca 개체군에 동일하게 적용된다는 뜻도 아니다."
    if v=="Official crop identity does not establish tortoise feeding safety, oxalate effect, dose, percentage or frequency.":
        return "공식 작물 동정 자료는 육지거북 급여 안전성·옥살산염 영향·급여량·식단 비율·급여 빈도를 입증하지 않는다."
    if v=="Does not by itself establish toxicological safety, species-level equivalence across a genus, exact captive feeding percentages, or replace peer-reviewed evidence.":
        return "이 자료만으로 독성학적 안전성, 같은 속의 모든 종을 똑같이 볼 근거 또는 정확한 사육 식단 비율을 확정할 수 없으며 동료평가 연구를 대체하지도 않는다."
    if v=="In-vitro cytotoxicity of concentrated essential oil does not establish fresh-leaf oral toxicity, a tortoise toxic dose, or an accidental-exposure outcome.":
        return "농축 정유의 시험관 내 세포독성 결과만으로 생잎을 먹었을 때의 독성, 육지거북에서 독성이 나타나는 양 또는 우발 섭취 결과를 판단할 수 없다."
    if v=="Rhizome/root extract findings must not be converted into a fresh flower, fruit or leaf toxic dose for tortoises.":
        return "뿌리줄기·뿌리 추출물 결과를 육지거북이 생꽃·생열매·생잎을 먹었을 때의 독성 용량으로 환산하면 안 된다."
    if v=="Does not establish Mediterranean Testudo-specific dose, feeding frequency, diet percentage, unlimited use, or equivalence of the fruit with the leaves.":
        return "지중해 Testudo에 한정된 급여량·빈도·식단 비율·무제한 급여를 정하는 자료가 아니며 열매와 잎을 똑같이 취급할 근거도 아니다."
    if v=="Does not establish a staple percentage, unlimited feeding, Mediterranean Testudo-specific dose, or safety of similarly named Hypericum species.":
        return "주식 비율·무제한 급여·지중해 Testudo에 한정된 급여량을 정하지 않으며 이름이 비슷한 다른 Hypericum 종의 안전성까지 입증하지 않는다."
    if v=="Does not establish a Mediterranean Testudo-specific percentage or unlimited use; the entry distinguishes leaves from fruit and also spans more than one plant taxon.":
        return "지중해 Testudo에 한정된 식단 비율이나 무제한 급여를 정하는 자료가 아니다. 출처는 잎과 열매를 구분하며 둘 이상의 식물 분류군을 함께 다루므로 부위·분류군 경계를 유지해야 한다."
    if v=="Does not establish that the entire plant is systemically toxic to Testudo graeca ibera. Leaf/sap irritation and the separate high-sugar fruit issue must not be conflated.":
        return "식물 전체가 이베라그리스육지거북에 전신 독성을 일으킨다는 뜻은 아니다. 잎·수액의 자극성 문제와 별개의 고당도 열매 문제를 서로 혼동하면 안 된다."
    if v=="Does not establish that every Poaceae species is safe, nor an Ibera-specific grass percentage, fixed frequency, unlimited use, or equivalence between young grass and mature grain/seed.":
        return "모든 벼과 식물이 안전하다는 뜻이 아니며 이베라그리스육지거북의 풀 식단 비율·정해진 급여 빈도·무제한 급여도 정하지 않는다. 어린 풀과 성숙한 곡립·씨앗을 똑같이 취급하면 안 된다."
    if v=="Does not support feeding pods or beans, unlimited feeding, or an Ibera-specific quantitative dose.":
        return "꼬투리나 콩알의 급여, 무제한 급여 또는 이베라그리스육지거북의 구체적인 급여량을 뒷받침하는 자료는 아니다."
    if v=="Excludes pyrethrin-rich C. cinerariifolium and C. coccineum; does not establish an Ibera-specific dose.":
        return "피레트린 함량이 높은 C. cinerariifolium과 C. coccineum은 제외하며 이베라그리스육지거북에 한정된 급여량을 정하는 자료도 아니다."
    if v=="This is not a controlled Testudo graeca ibera feeding trial and does not establish a captive feeding percentage, fixed frequency, unlimited use, or a tortoise-specific toxic dose.":
        return "통제된 이베라그리스육지거북 급여시험이 아니므로 사육 식단 비율·정해진 급여 빈도·무제한 급여·육지거북에 한정된 독성 용량을 정할 수 없다."
    if v=="This specialist database entry is not a controlled Testudo graeca ibera feeding/toxicity trial. Do not convert its category into an exact captive percentage, fixed frequency, toxic dose, unlimited-use claim, or safety equivalence for unlisted plant parts or related taxa.":
        return "이 전문 DB 항목은 통제된 이베라그리스육지거북 급여·독성시험이 아니다. 분류 등급을 정확한 사육 식단 비율·정해진 급여 빈도·독성 용량·무제한 급여 또는 명시되지 않은 식물 부위·관련 분류군의 안전성으로 환산하면 안 된다."
    if v=="The mechanism discussion is not a Testudo graeca ibera dose-response or harm trial. The record does not independently establish a tortoise toxic dose or convert the composition rationale into proven poisoning.":
        return "기전 설명은 이베라그리스육지거북의 용량-반응 또는 위해 시험이 아니다. 이 자료만으로 육지거북 독성 용량을 정하거나 성분상의 우려를 실제 중독이 입증된 것으로 바꿔 해석할 수 없다."
    if v=="This is not a Mediterranean Testudo or Testudo graeca ibera feeding trial and does not establish a Brassica juncea-specific percentage, frequency or unrestricted use.":
        return "지중해 Testudo 또는 이베라그리스육지거북 급여시험이 아니며 Brassica juncea에 한정된 식단 비율·급여 빈도나 무제한 급여 허용 범위를 정하는 자료는 아니다."
    if v=="Master concept is Taraxacum spp.; this record must not be generalized to every Taraxacum species and does not establish Ibera-specific dose, percentage, or fixed frequency.":
        return "마스터 개념은 Taraxacum spp.이다. 이 기록을 모든 Taraxacum 종에 일반화하면 안 되며 이베라그리스육지거북에 한정된 급여량·식단 비율·정해진 급여 빈도를 정하지 않는다."
    if v=="Must not be transferred to Tagetes marigolds; does not establish Ibera-specific percentage, fixed frequency, or unlimited use.":
        return "이 판정을 Tagetes 메리골드에 그대로 적용하면 안 된다. 이베라그리스육지거북에 한정된 식단 비율·정해진 급여 빈도·무제한 급여도 정하지 않는다."
    if v=="Does not establish a Testudo graeca ibera-specific percentage, fixed frequency, essential-oil safety, or unlimited intake.":
        return "이베라그리스육지거북에 한정된 식단 비율·정해진 급여 빈도·정유 안전성·무제한 섭취를 정하는 자료는 아니다."
    if v=="Does not establish a Testudo graeca ibera-specific dose, fixed frequency, or equivalence to other Salvia species.":
        return "이베라그리스육지거북에 한정된 급여량·정해진 급여 빈도를 정하지 않으며 다른 Salvia 종에도 같은 판정을 적용할 근거는 아니다."
    if v=="Genus-level guidance does not establish a Testudo graeca ibera-specific percentage, fixed frequency, refined essential-oil safety, or unlimited intake.":
        return "속 수준 지침만으로 이베라그리스육지거북의 식단 비율·구체적인 급여 빈도·정제 정유의 안전성이나 무제한 섭취 허용 범위를 정할 수 없다."
    if v=="Does not establish a Testudo graeca ibera-specific toxic dose or prove identical hazard magnitude for every Muscari species and plant part.":
        return "이베라그리스육지거북에 한정된 독성 용량을 정하지 않으며 모든 Muscari 종과 식물 부위의 위해 정도가 동일하다는 사실도 입증하지 않는다."
    if v=="Does not establish a Testudo graeca ibera-specific intake percentage or prove every cultivar/endophyte state equivalent.":
        return "이베라그리스육지거북에 한정된 섭취 비율을 정하지 않으며 모든 품종과 내생균 상태를 똑같이 볼 근거도 아니다."
    if v=="Does not quantify a safe or toxic dose for young broccoli microgreens or Testudo graeca ibera.":
        return "어린 브로콜리 마이크로그린 또는 이베라그리스육지거북에 대한 안전하게 먹을 수 있는 양이나 독성이 나타나는 양을 정량화한 자료는 아니다."
    if v=="Does not establish tortoise toxicity, a tortoise safe dose, or that all glucosinolates have the same biological effect.":
        return "육지거북에서 독성이 나타나는 양이나 안전한 섭취량을 정하는 자료가 아니며 모든 글루코시놀레이트가 동일한 생물학적 효과를 가진다는 뜻도 아니다."
    if v=="Does not directly test mizuna, tatsoi or komatsuna cultivars, and does not establish an Ibera-specific feeding percentage.":
        return "미즈나·타쵸이·코마츠나 품종을 직접 시험한 자료가 아니며 이베라그리스육지거북에 한정된 급여 비율도 정하지 않는다."
    if v=="Does not provide a Malva verticillata-specific intake percentage or an Ibera-specific quantitative trial.":
        return "Malva verticillata에 한정된 섭취 비율이나 이베라그리스육지거북 대상 정량시험을 제공하지 않는다."
    if v=="The same source says it is not suitable as feed; it does not establish tortoise feeding suitability or quantity.":
        return "같은 출처가 사료로 적합하지 않다고 명시한다. 이 자료로 육지거북 급여 적합성이나 급여량을 정할 수 없다."
    if v=="Does not establish captive diet percentage, feeding frequency, unlimited use, or a direct Testudo graeca ibera safety dose.":
        return "사육 식단 비율·급여 빈도·무제한 급여 또는 이베라그리스육지거북의 안전한 섭취량을 직접 정하는 자료는 아니다."
    if v=="Does not establish a toxic dose, clinical toxicity, safe captive feeding percentage, or Testudo-specific adverse effect.":
        return "독성 용량·임상 독성·안전한 사육 식단 비율 또는 Testudo에 한정된 이상반응을 확정하는 자료는 아니다."
    if v=="Does not establish a Testudo graeca ibera toxic dose, clinical poisoning threshold, or that an accidental bite causes poisoning.":
        return "이베라그리스육지거북의 독성 용량·임상 중독 역치를 정하지 않으며 우발적으로 한입 먹었다는 사실만으로 중독이 발생한다고 입증하지도 않는다."
    if v=="This does not establish an Ibera-specific feeding percentage, fixed frequency, unlimited use, or equivalence with unrelated plants called mallow. The Korean retail concept 아욱 still needs species-level mapping before an exact-taxon conclusion.":
        return "이베라그리스육지거북에 한정된 급여 비율·정해진 급여 빈도·무제한 급여를 정하지 않으며, 이름에 mallow가 들어간다는 이유만으로 무관한 식물에 같은 판정을 적용할 수 없다. 국내 유통명 ‘아욱’은 정확한 종 수준 결론 전에 종 동정 연결이 필요하다."
    if v=="Does not establish a Testudo graeca ibera-specific dose, fixed frequency, or equivalence to other Salvia species.":
        return "이베라그리스육지거북에 한정된 급여량·정해진 급여 빈도를 정하지 않으며 다른 Salvia 종에도 같은 판정을 적용할 근거는 아니다."
    if v=="Does not support feeding pods or beans, unlimited feeding, or an Ibera-specific quantitative dose.":
        return "꼬투리나 콩알 급여·무제한 급여 또는 이베라그리스육지거북에 한정된 정량 급여량을 뒷받침하지 않는다."
    # Common quantitative/scope limitations.
    if v in {
        "Does not establish a Testudo graeca ibera-specific dose, fixed frequency, diet percentage, toxic dose, or unlimited feeding allowance. Apply only within the stated taxon and plant-part scope.",
        "Does not establish a Testudo graeca ibera-specific dose, fixed frequency, diet percentage, toxic dose, or unlimited feeding allowance; apply only within the stated taxon and plant-part scope.",
    }:
        return "이 자료만으로 이베라그리스육지거북(T. g. ibera)의 해당 종에 한정된 급여량·정해진 급여 빈도·식단 비율·독성 용량·무제한 급여 허용을 정할 수 없다. 명시된 분류군과 식물 부위 범위 안에서만 적용한다."
    if v in {
        "Does not establish a Testudo graeca ibera-specific dose, fixed diet percentage, toxic dose, or unlimited feeding allowance; do not transfer the verdict to unlisted plant parts or related taxa.",
        "Does not establish a Testudo graeca ibera-specific dose, fixed diet percentage, toxic dose, or unlimited feeding allowance; do not transfer the verdict beyond the stated taxon and plant-part scope.",
        "Does not establish a Testudo graeca ibera-specific dose, fixed diet percentage, toxic dose, or unlimited feeding allowance; do not transfer beyond the stated taxon and plant-part scope.",
    }:
        return "이 자료만으로 이베라그리스육지거북(T. g. ibera)의 해당 종에 한정된 급여량·구체적인 식단 비율·독성 용량·무제한 급여 허용을 정할 수 없다. 판정을 명시되지 않은 식물 부위·관련 분류군 또는 제시된 범위 밖으로 확대하지 않는다."
    if v=="Does not establish Mediterranean Testudo-specific dose, exact feeding frequency, diet percentage, or unlimited use.":
        return "지중해 Testudo에 한정된 급여량·정확한 급여 빈도·식단 비율·무제한 급여를 정하는 자료는 아니다."
    if v=="Not a controlled Testudo graeca ibera trial; does not establish an exact percentage, fixed frequency, toxic dose, or unlimited use.":
        return "통제된 이베라그리스육지거북 급여시험이 아니므로 정확한 식단 비율·정해진 급여 빈도·독성 용량·무제한 급여를 정할 수 없다."
    if v=="No tortoise-specific feeding threshold or dose.":
        return "육지거북에 한정된 급여 임계값이나 용량을 정하는 자료는 아니다."
    if v=="Does not directly determine captive feeding quantity for Testudo graeca ibera.":
        return "이베라그리스육지거북의 사육 환경 급여량을 직접 결정하는 자료는 아니다."
    if v=="Does not establish tortoise-specific safety or feeding quantity.":
        return "육지거북에 한정된 안전성이나 급여량을 확정하는 자료는 아니다."
    if v=="Does not establish tortoise feeding safety or nutritional suitability.":
        return "육지거북 급여 안전성이나 영양학적 적합성을 확정하는 자료는 아니다."
    if v=="Does not establish tortoise-specific suitability or captive feeding quantity.":
        return "육지거북에 한정된 적합성이나 사육 환경 급여량을 확정하는 자료는 아니다."
    if v=="Does not establish oral feeding safety, digestibility, dose, or suitability for tortoises.":
        return "육지거북의 경구 급여 안전성·소화성·용량·적합성을 확정하는 자료는 아니다."

    # Plant-part-scope records use a fixed public pattern; keep the scope boundary explicit.
    m=re.fullmatch(r"Classifies the stated (.+?) plant-part scope as (Safe to Feed|Feed in Moderation|Feed Sparingly|Do not Feed)\.",v)
    if m:
        label={"Safe to Feed":"급여 가능","Feed in Moderation":"제한 급여","Feed Sparingly":"소량·드물게 급여","Do not Feed":"급여하지 않음"}[m.group(2)]
        return f"출처는 명시된 {m.group(1)} 식물 부위 범위를 {label}으로 분류한다. 이 판정을 다른 식물 부위로 확대하지 않는다."
    m=re.fullmatch(r"Classifies the (.+?) tree entry as (Safe to Feed|Feed in Moderation|Feed Sparingly|Do not Feed)\.",v)
    if m:
        label={"Safe to Feed":"급여 가능","Feed in Moderation":"제한 급여","Feed Sparingly":"소량·드물게 급여","Do not Feed":"급여하지 않음"}[m.group(2)]
        return f"출처는 {m.group(1)} 나무 항목을 {label}으로 분류한다."
    # Specialist-database classification sentences: localize the classification while retaining taxa/part qualifiers.
    m=re.fullmatch(r"Classifies (.+?) as (Safe to Feed|Feed in Moderation|Feed Sparingly|Do not Feed)\.",v)
    if m:
        label={"Safe to Feed":"급여 가능","Feed in Moderation":"제한 급여","Feed Sparingly":"소량·드물게 급여","Do not Feed":"급여하지 않음"}[m.group(2)]
        return f"출처는 {m.group(1)} 항목을 {label}으로 분류한다."
    m=re.fullmatch(r"Kew Plants of the World Online lists (.+?) as an accepted species name\.",v)
    if m:
        return f"Kew Plants of the World Online은 {m.group(1)}을(를) 인정되는 종명으로 등재한다. 이는 식물 동정 근거이며 급여 안전성 근거는 아니다."
    # Final reader-facing guard for newly added evidence sentences.
    for raw,label in (
        ("Feed in Moderation","제한 급여"),
        ("Feed Sparingly","소량·드물게 급여"),
        ("Do not Feed","급여하지 않음"),
        ("Safe to Feed","급여 가능"),
    ):
        v=v.replace(raw,label)
    if re.search(r"[A-Za-z]{3,}", v) and not re.search(r"[가-힣]", v):
        return "이 자료는 해당 식물의 동정·성분·야생 섭식 또는 전문 사육 지침 가운데 명시된 근거 범위를 뒷받침한다. 구체적인 급여 판정은 위 판정 카드와 아래 적용 한계를 함께 확인한다."
    return v

def evidence_limit_display(value):
    v=str(value or "").strip()
    mixed_ko={
        "This does not establish an Ibera-specific feeding percentage, fixed frequency, unlimited use, or equivalence with unrelated plants called mallow. The Korean retail concept 아욱 still needs species-level mapping before an exact-taxon conclusion.":"이 자료는 이베라그리스육지거북에 한정된 급여 비율·정해진 급여 빈도·무제한 급여를 확정하지 않으며, ‘mallow’라고 불리는 무관한 식물까지 같은 판정을 적용할 근거도 없다. 국내 유통명 ‘아욱’은 정확한 분류군 결론을 내리기 전에 종 수준의 확인이 더 필요하다.",
        "The conclusion must not be expanded to Mentha spp. as a whole. The same source separately excludes peppermint (Mentha × piperita) and pennyroyal (Mentha pulegium); therefore a generic Korean '민트' product requires species identification before a feeding conclusion.":"이 결론을 Mentha속 전체로 확대하면 안 된다. 같은 출처는 페퍼민트(Mentha × piperita)와 페니로열(Mentha pulegium)을 별도로 제외하므로, 국내에서 ‘민트’라는 일반명으로 판매되는 제품은 급여 결론 전에 종 확인이 필요하다.",
    }
    if v in mixed_ko:
        return mixed_ko[v]
    exact={
        "This source does not by itself establish an exact captive feeding percentage, fixed frequency, unlimited use, or safety equivalence beyond the animal taxon, plant identity and plant part actually covered by the source.":"이 자료 하나만으로 정확한 사육 급여 비율·정해진 급여 빈도·무제한 급여 또는 자료가 실제로 다룬 동물 분류군·식물 정체성·식물 부위를 까지 똑같이 안전하다고 확대 해석할 수 없다.",
        "Specialist plant-database guidance is not a controlled Testudo graeca ibera feeding or toxicity trial. It does not establish an exact captive percentage, fixed frequency, unlimited use, or safety equivalence for unlisted plant parts or related taxa.":"전문 식물 DB 지침은 이베라그리스육지거북의 통제된 급여·독성시험이 아니다. 정확한 사육 급여 비율·정해진 급여 빈도·무제한 급여 또는 명시되지 않은 식물 부위·근연 분류군까지 똑같이 안전하다고 볼 근거는 아니다.",
        "This specialist database entry is not a controlled Testudo graeca ibera feeding/toxicity trial. Its category must not be converted into an exact captive percentage, fixed frequency, toxic dose, unlimited-use claim, or safety equivalence for unlisted plant parts or related taxa.":"이 전문 DB 항목은 이베라그리스육지거북의 통제된 급여·독성시험이 아니다. 해당 분류를 정확한 사육 급여 비율·정해진 급여 빈도·독성 용량·무제한 급여 또는 명시되지 않은 식물 부위·근연 분류군까지 똑같이 안전하다는 뜻으로 해석하면 안 된다.",
        "This record must not be used beyond its stated evidence domain. Plant identity or chemistry evidence does not itself prove tortoise feeding safety; related-taxon husbandry does not establish Testudo graeca ibera-specific dose, frequency, percentage, or unlimited use.":"이 기록은 명시된 근거 범위를 넘어 사용하면 안 된다. 식물 동정·성분 자료 자체는 육지거북 급여 안전성을 증명하지 않으며, 근연 분류군의 사육자료만으로 이베라그리스육지거북의 급여량·빈도·식단 비율이나 무제한 급여 허용 범위를 정할 수 없다.",
        "This migrated record preserves the existing assessment/source scope. It is not a controlled Testudo graeca ibera feeding/toxicity trial and does not establish an exact percentage, fixed frequency, toxic dose, unlimited use, or safety equivalence across unlisted plant parts/taxa.":"이 기록은 기존 판정과 출처의 적용 범위를 그대로 유지한다. 이베라그리스육지거북의 통제된 급여·독성시험이 아니며 정확한 급여 비율·정해진 급여 빈도·독성 용량·무제한 급여 또는 명시되지 않은 식물 부위·분류군이 모두 똑같이 안전하다고 볼 근거는 아니다.",
        "Taxonomic acceptance does not establish tortoise feeding safety, dose, frequency, diet percentage, or plant-part equivalence.":"분류학적으로 인정된 식물이라는 사실은 육지거북 급여 안전성·급여량·빈도·식단 비율 또는 식물 부위를 서로 똑같이 볼 근거는 아니다.",
        "No Ibera-specific dose, fixed diet percentage, or unlimited feeding allowance.":"이 자료만으로 이베라그리스육지거북의 구체적인 급여량·식단 비율이나 무제한 급여 허용 범위를 정할 수 없다.",
    }
    if v in exact:
        return exact[v]
    # High-frequency scope templates. Preserve every substantive boundary while localizing the reader-facing copy.
    if v.startswith("Does not establish a Testudo graeca ibera-specific dose"):
        tail=[]
        if "fixed frequency" in v: tail.append("정해진 급여 빈도")
        if "fixed diet percentage" in v or "diet percentage" in v: tail.append("구체적인 식단 비율")
        if "toxic dose" in v: tail.append("독성 용량")
        if "unlimited feeding allowance" in v: tail.append("무제한 급여 허용 범위")
        base="이 자료는 이베라그리스육지거북에 한정된 급여량"
        if tail: base+="·"+"·".join(tail)
        base+="을 확정하지 않는다."
        if "stated taxon and plant-part scope" in v:
            base+=" 명시된 동물 분류군과 식물 부위 범위 안에서만 적용한다."
        elif "unlisted plant parts or related taxa" in v:
            base+=" 원자료가 다루지 않은 식물 부위나 근연 분류군에 같은 판정을 그대로 적용하지 않는다."
        elif "beyond the stated taxon and plant-part scope" in v or "beyond the stated taxon and plant-part scope" in v:
            base+=" 명시된 동물 분류군과 식물 부위 범위를 넘어 판정을 확대하지 않는다."
        if "equivalence to other Salvia species" in v:
            base+=" 다른 Salvia 종에 같은 판정을 적용할 근거는 아니다."
        return base
    if v.startswith("Cattle toxicity cannot be converted"):
        return "소에서 확인된 독성 자료만으로 이베라그리스육지거북에서 독성이 나타나는 양·안전한 섭취량·급여 빈도나 식단 비율을 정할 수 없다. 또한 식용 들깨의 모든 품종이 같은 페릴라케톤 농도를 가진다고 볼 근거도 없다."
    if v.startswith("Does not by itself establish toxicological safety"):
        return "이 자료만으로 독성학적 안전성·같은 속의 모든 종을 똑같이 볼 근거·정확한 사육 급여 비율을 확정할 수 없으며, 동료평가 학술근거를 대체하지 않는다."
    if v.startswith("Does not demonstrate direct toxicity of sweet-potato leaves"):
        return "고구마 잎의 이베라그리스육지거북 직접 독성을 입증하지 않으며, 우발적 섭취를 곧 중독으로 볼 근거도 아니다. 잎과 덩이뿌리를 동일하게 취급하지 않는다."
    if v.startswith("Does not directly determine captive feeding quantity"):
        return "이 자료는 이베라그리스육지거북의 사육 환경의 급여량을 직접 정하는 근거는 아니다."
    if v.startswith("Does not directly test mizuna"):
        return "미즈나·타쏘이·코마츠나 품종을 직접 시험한 자료가 아니며, 이베라그리스육지거북에 한정된 급여 비율까지 정하는 근거는 아니다."
    if v.startswith("Does not establish Mediterranean Testudo-specific dose"):
        extra=" 과실과 잎의 안전성을 서로 동일하다고 보지 않는다." if "equivalence of the fruit with the leaves" in v else ""
        return "이 자료만으로 지중해 Testudo의 구체적인 급여량·급여 빈도·식단 비율이나 무제한 급여 허용 범위를 정할 수 없다."+extra
    if v.startswith("Does not establish a Mediterranean Testudo-specific percentage"):
        return "이 자료만으로 지중해 Testudo의 식단 비율이나 무제한 급여 허용 범위를 정할 수 없다. 잎과 과실을 구분하며 여러 식물 분류군의 내용을 서로 동일하게 적용하면 안 된다."
    if v.startswith("Does not establish a Testudo graeca ibera toxic dose"):
        return "이 자료만으로 이베라그리스육지거북에서 어느 양부터 독성이 나타나는지, 임상 중독이 시작되는 수준이 얼마인지 또는 우발적으로 한입 먹었을 때 중독되는지를 판단할 수 없다."
    if v.startswith("Does not establish a Testudo graeca ibera-specific diet percentage"):
        return "이 자료만으로 이베라그리스육지거북의 식단 비율·구체적인 급여 빈도나 무제한 급여 허용 범위를 정할 수 없다. 성숙한 씨앗은 어린 풀과 같지 않으며 단백질이 높아 먹이지 않도록 한 원자료의 경고를 따른다."
    if v.startswith("Does not establish a Testudo graeca ibera-specific feeding percentage"):
        return "이 자료는 이베라그리스육지거북에 한정된 급여 비율이나 정해진 급여 빈도를 정하는 근거는 아니다. 마른 씨앗 이삭은 풀·건초와 같지 않으며 눈이나 입에 상처를 낼 수 있어 제거하도록 한 원자료의 경고를 따른다."
    if v.startswith("Does not establish a Testudo graeca ibera-specific intake percentage"):
        return "이 자료만으로 이베라그리스육지거북의 구체적인 섭취 비율을 정할 수 없으며, 모든 품종과 내생균 상태를 똑같이 볼 근거도 아니다."
    if v.startswith("Does not establish a Testudo graeca ibera-specific percentage"):
        base = "이 자료는 이베라그리스육지거북에 한정된 급여 비율·정해진 급여 빈도·무제한 급여 등 해당 문헌이 직접 확인하지 않은 구체적인 안전 급여 범위를 보장하지 않는다."
        if "possible laxative effect" in v:
            base += " 원자료 자체도 완하 작용 가능성 때문에 과량 급여를 경고한다."
        if "essential-oil safety" in v:
            base += " 정유가 안전하다고 판단할 근거도 아니다."
        return base
    if v.startswith("Does not establish a Testudo graeca ibera-specific toxic dose"):
        return "이 자료만으로 이베라그리스육지거북에서 어느 양부터 독성이 나타나는지 알 수 없으며 모든 관련 종과 식물 부위의 위해 정도가 동일하다고 증명하지 않는다."
    if v.startswith("Does not establish a staple percentage"):
        return "이 자료는 주식 비율·무제한 급여·지중해 Testudo에 한정된 급여량 또는 이름이 비슷한 근연종까지 안전하다고 볼 근거는 아니다."
    if v.startswith("Does not establish a toxic dose"):
        return "이 자료는 어느 양부터 독성이 나타나는지, 실제 임상 독성이 발생하는지, 안전한 사육 급여 비율이 얼마인지 또는 Testudo에서 어떤 이상반응이 나타나는지를 이 자료만으로 판단할 수 없다."
    if v.startswith("Does not establish an Ibera-specific percentage"):
        return "이 자료는 이베라그리스육지거북에 한정된 급여 비율이나 빈도를 확정하지 않으며 같은 일반명 때문에 다른 식물 분류군에 판정을 옮겨 적용하면 안 된다."
    if v.startswith("Does not establish captive diet percentages"):
        return "이 자료만으로 사육 식단 비율·급여 빈도나 무제한 급여 허용 범위를 정할 수 없으며, 해당 속의 모든 종이 똑같이 안전하다고 볼 근거도 아니다."
    if v.startswith("Does not establish captive diet percentage"):
        return "이 자료는 사육 식단 비율·급여 빈도·무제한 급여 또는 이베라그리스육지거북에 대한 안전한 섭취량을 정하는 근거는 아니다."
    exact_more={
        "Does not establish oral feeding safety, digestibility, dose, or suitability for tortoises.":"이 자료만으로 먹었을 때의 안전성·소화 가능성·적정 급여량이나 육지거북 먹이로서의 적합성을 판단할 수 없다.",
        "Does not establish safety for Testudo graeca ibera, a tortoise feeding dose or frequency, or justify transferring toxicity of other Oenanthe species to O. javanica. It also does not prove that O. javanica is safe as a captive tortoise food.":"이베라그리스육지거북에 대한 안전성·급여량·급여 빈도를 확정하지 않는다. 다른 Oenanthe 종의 독성을 O. javanica에 그대로 적용할 수도 없으며, O. javanica가 사육 육지거북 먹이로 안전하다는 증거도 아니다.",
        "Does not establish that every Poaceae species is safe, nor an Ibera-specific grass percentage, fixed frequency, unlimited use, or equivalence between young grass and mature grain/seed.":"모든 벼과 식물이 안전하다는 뜻은 아니며, 이 자료만으로 이베라그리스육지거북의 풀 급여 비율·구체적인 급여 빈도나 무제한 급여 허용 범위를 정할 수 없다. 어린 풀과 성숙한 곡립·씨앗을 같은 먹이로 취급할 근거도 아니다.",
        "Does not establish that the entire plant is systemically toxic to Testudo graeca ibera. Leaf/sap irritation and the separate high-sugar fruit issue must not be conflated.":"이 자료만으로 식물 전체가 이베라그리스육지거북에 전신 독성을 일으킨다고 판단할 수 없다. 잎·수액의 자극성과 별개의 고당도 과실 문제를 혼동하면 안 된다.",
        "Does not establish tortoise feeding safety or nutritional suitability.":"육지거북에게 안전한 먹이인지, 영양학적으로 적합한지를 이 자료만으로 판단할 수 없다.",
        "Does not establish tortoise toxicity, a tortoise safe dose, or that all glucosinolates have the same biological effect.":"육지거북에서 독성이 나타나는 양이나 안전한 섭취량을 정하는 자료가 아니며 모든 글루코시놀레이트가 같은 생물학적 효과를 가진다고 볼 수도 없다.",
        "Does not establish tortoise-specific safety or feeding quantity.":"육지거북에 한정된 안전성이나 급여량을 정하는 근거는 아니다.",
        "Does not establish tortoise-specific suitability or captive feeding quantity.":"육지거북에 한정된 적합성이나 사육 환경 급여량을 정하는 근거는 아니다.",
        "Does not provide a Malva verticillata-specific intake percentage or an Ibera-specific quantitative trial.":"Malva verticillata에 한정된 섭취 비율이나 이베라그리스육지거북 대상 정량시험을 제공하지 않는다.",
        "Does not quantify a safe or toxic dose for young broccoli microgreens or Testudo graeca ibera.":"어린 브로콜리 마이크로그린 또는 이베라그리스육지거북에 대한 안전·독성 용량을 정량화하지 않는다.",
        "Does not support feeding pods or beans, unlimited feeding, or an Ibera-specific quantitative dose.":"꼬투리·콩 급여, 무제한 급여 또는 이베라그리스육지거북에 한정된 정량 급여량을 뒷받침하지 않는다.",
        "Excludes pyrethrin-rich C. cinerariifolium and C. coccineum; does not establish an Ibera-specific dose.":"피레트린 함량이 높은 C. cinerariifolium과 C. coccineum은 제외한다. 이베라그리스육지거북에 한정된 급여량도 확정하지 않는다.",
        "Genus-level guidance does not establish a Testudo graeca ibera-specific percentage, fixed frequency, refined essential-oil safety, or unlimited intake.":"속 수준의 지침은 이베라그리스육지거북에 한정된 급여 비율·정해진 급여 빈도·정제 정유의 안전성 또는 무제한 섭취를 확정하지 않는다.",
        "In-vitro cytotoxicity of concentrated essential oil does not establish fresh-leaf oral toxicity, a tortoise toxic dose, or an accidental-exposure outcome.":"농축 정유의 시험관 내 세포독성은 신선한 잎의 경구 독성·육지거북 독성 용량 또는 우발적 노출의 결과를 확정하지 않는다.",
        "Master concept is Taraxacum spp.; this record must not be generalized to every Taraxacum species and does not establish Ibera-specific dose, percentage, or fixed frequency.":"기준 개념은 Taraxacum spp.이다. 이 기록을 모든 Taraxacum 종에 일반화하면 안 되며 이베라그리스육지거북에 한정된 급여량·비율·정해진 급여 빈도도 확정하지 않는다.",
        "Must not be transferred to Tagetes marigolds; does not establish Ibera-specific percentage, fixed frequency, or unlimited use.":"Tagetes 계열 메리골드에 판정을 옮겨 적용하면 안 된다. 이베라그리스육지거북에 한정된 급여 비율·정해진 급여 빈도·무제한 급여도 확정하지 않는다.",
        "No tortoise-specific feeding threshold or dose.":"육지거북에 한정된 급여 역치나 급여량은 확정되어 있지 않다.",
        "Non-quantitative observations do not establish captive diet ratios, feeding frequency, or species-level equivalence for Korean plants within the same genus.":"비정량 관찰 자료만으로 사육 식단 비율·급여 빈도를 정할 수 없으며, 같은 속에 속한다는 이유만으로 국내 식물 종에 같은 판정을 적용할 수도 없다.",
        "Not a controlled Testudo graeca ibera trial; does not establish an exact percentage, fixed frequency, toxic dose, or unlimited use.":"이베라그리스육지거북을 대상으로 한 통제시험이 아니며 정확한 급여 비율·정해진 급여 빈도·독성 용량·무제한 급여를 확정하지 않는다.",
        "Official crop identity does not establish tortoise feeding safety, oxalate effect, dose, percentage or frequency.":"공식 작물 동정 정보는 육지거북 급여 안전성·옥살산염의 영향·급여량·비율·빈도를 확정하지 않는다.",
    }
    if v in exact_more:
        return exact_more[v]
    exact_final={
        "Rhizome/root extract findings must not be converted into a fresh flower, fruit or leaf toxic dose for tortoises.":"뿌리줄기·뿌리 추출물 연구 결과를 육지거북이 신선한 꽃·과실·잎을 섭취할 때의 독성 용량으로 환산하면 안 된다.",
        "The mechanism discussion is not a Testudo graeca ibera dose-response or harm trial. The record does not independently establish a tortoise toxic dose or convert the composition rationale into proven poisoning.":"기전 설명은 이베라그리스육지거북의 용량-반응 또는 위해성 시험이 아니다. 이 기록만으로 육지거북의 독성 용량을 확정하거나 성분상의 우려를 실제 중독이 입증된 것으로 바꾸어 해석할 수 없다.",
        "The same source says it is not suitable as feed; it does not establish tortoise feeding suitability or quantity.":"같은 출처에서 사료로 적합하지 않다고 명시한다. 육지거북 급여 적합성이나 급여량을 확정하는 자료가 아니다.",
        "This is a genus-level caution, not an Oenanthe javanica-specific Testudo graeca ibera toxicity study or dose-response experiment. It does not establish a tortoise toxic dose for Korean minari.":"속 수준의 주의 근거이며 Oenanthe javanica를 대상으로 한 이베라그리스육지거북 독성·용량반응 시험이 아니다. 국내 미나리를 육지거북이 어느 정도 먹었을 때 독성이 나타나는지는 이 자료로 알 수 없다.",
        "This is genus-level evidence, not an Artemisia princeps-specific Testudo trial. It does not establish identical chemistry across Artemisia species or a tortoise toxic dose.":"속 수준의 근거이며 Artemisia princeps를 대상으로 한 Testudo 시험이 아니다. Artemisia 각 종의 화학조성이 동일하다고 확정하지 않으며 육지거북 독성 용량도 제시하지 않는다.",
        "This is not a Mediterranean Testudo or Testudo graeca ibera feeding trial and does not establish a Brassica juncea-specific percentage, frequency or unrestricted use.":"지중해 Testudo 또는 이베라그리스육지거북 급여시험이 아니며 Brassica juncea의 급여 비율·빈도·제한 없는 급여를 확정하지 않는다.",
        "This is not a Testudo graeca ibera feeding-safety study and does not establish tortoise-specific safety, dose, frequency, percentage, or a single composition value for unidentified Korean-market mulberry leaves.":"이베라그리스육지거북 급여 안전성 연구가 아니다. 육지거북에 한정된 안전성·급여량·빈도·비율을 확정하지 않으며, 종이 확인되지 않은 국내 유통 뽕잎에 하나의 성분값을 일괄 적용할 수도 없다.",
        "This is not a controlled Testudo graeca ibera feeding trial and does not establish a captive feeding percentage, fixed frequency, unlimited use, or a tortoise-specific toxic dose.":"이베라그리스육지거북을 대상으로 한 통제 급여시험이 아니며 사육 급여 비율·정해진 급여 빈도·무제한 급여 또는 육지거북에 한정된 독성 용량을 확정하지 않는다.",
        "This is not an exact-taxon Testudo graeca ibera trial. Historical-name linkage must not be used to transfer the conclusion to Chrysanthemum cinerariifolium, C. coccineum or unrelated taxa.":"정확한 분류군의 이베라그리스육지거북 시험이 아니다. 과거 학명 연결만을 근거로 결론을 Chrysanthemum cinerariifolium, C. coccineum 또는 무관한 분류군에 옮겨 적용하면 안 된다.",
        "This plant-chemistry study is not a tortoise feeding trial. It does not establish a Testudo graeca ibera toxic threshold, safe intake, frequency, or that all edible perilla cultivars contain equivalent perilla-ketone concentrations.":"이 식물화학 연구는 육지거북 급여시험이 아니다. 이베라그리스육지거북의 독성 역치·안전 섭취량·급여 빈도를 확정하지 않으며 모든 식용 들깨 품종의 페릴라케톤 농도가 같다고 볼 수도 없다.",
        "This specialist database entry is not a controlled Testudo graeca ibera feeding/toxicity trial. Do not convert its category into an exact captive percentage, fixed frequency, toxic dose, unlimited-use claim, or safety equivalence for unlisted plant parts or related taxa.":"이 전문 DB 항목은 이베라그리스육지거북의 통제 급여·독성시험이 아니다. 해당 분류를 정확한 사육 급여 비율·정해진 급여 빈도·독성 용량·무제한 급여 또는 명시되지 않은 식물 부위·근연 분류군까지 똑같이 안전하다는 뜻으로 해석하면 안 된다.",
        "This specialist plant-database entry is not a controlled Testudo graeca ibera feeding or toxicity trial. Common-name similarity must not be used to transfer the verdict to a different genus or species, and the category does not define an exact captive percentage, fixed frequency or unlimited use.":"이 전문 식물 DB 항목은 이베라그리스육지거북의 통제 급여·독성시험이 아니다. 일반명이 비슷하다는 이유로 다른 속·종에 판정을 옮기면 안 되며, 해당 분류는 정확한 사육 급여 비율·정해진 급여 빈도·무제한 급여를 규정하지 않는다.",
        "This specialist verdict is not a Testudo graeca ibera toxicity trial. It does not establish a tortoise toxic dose, identical susceptibility to mammals, or identical perilla-ketone content across edible cultivars.":"이 전문 판정은 이베라그리스육지거북 독성시험이 아니다. 육지거북 독성 용량, 포유류와 동일한 감수성 또는 모든 식용 품종의 동일한 페릴라케톤 함량을 확정하지 않는다.",
        "Wild consumption does not establish unlimited captive feeding, a precise ration, or equivalence for every Testudo graeca population.":"야생 섭식 관찰만으로 사육 환경의 무제한 급여나 정확한 식단 비율을 정할 수 없으며, 모든 Testudo graeca 개체군에 똑같이 적용된다고 볼 수도 없다.",
    }
    if v in exact_final:
        return exact_final[v]
    # Korean mode: never expose a wholly untranslated evidence limitation.
    if re.search(r"[A-Za-z]{3,}", v) and not re.search(r"[가-힣]", v):
        return "이 자료만으로 육지거북의 정확한 급여량·정해진 급여 빈도·식단 비율·독성 용량·무제한 급여 또는 자료가 직접 다루지 않은 식물 부위·근연 분류군의 안전성을 확정할 수 없다. 원자료가 실제로 다룬 범위 안에서만 적용한다."
    return v

def evidence_role(e):
    t=str(e.get("source_type") or "")
    if "taxonomy" in t or "taxonomic" in t or "botanical" in t or "biodiversity" in t or "agriculture" in t:
        return "식물의 이름·분류·정체성을 확인하는 보조자료 — 급여 안전성 자체를 증명하지 않음"
    if "nutrition" in t or "food_composition" in t:
        return "성분을 확인하는 참고자료 — 급여 안전성 자체를 증명하지 않음"
    if e.get("directness")=="direct":
        return "급여 판정에 직접 연결되는 근거"
    return "급여 판정을 보조하는 간접·맥락 근거"

def related_for(p,limit=6):
    same_family=[x for x in plants if x["id"]!=p["id"] and x.get("family") and x.get("family")==p.get("family")]
    same_category=[x for x in plants if x["id"]!=p["id"] and x.get("category") and x.get("category")==p.get("category") and x not in same_family]
    return (same_family+same_category)[:limit]

CSS='''
:root{--bg:#f6f8f5;--card:#fff;--line:#dce5dd;--text:#17231b;--muted:#5f6c63;--forest:#235f3e;--green:#e7f5eb;--yellow:#fff7df;--hold:#f1f3f2;--danger:#fdeaea}
*{box-sizing:border-box}body{font-family:system-ui,-apple-system,"Noto Sans KR",sans-serif;max-width:920px;margin:auto;padding:18px 22px 40px;line-height:1.62;color:var(--text);background:var(--bg)}
a{color:inherit}a:focus-visible,button:focus-visible{outline:3px solid rgba(40,106,70,.28);outline-offset:3px}
.skiplink{position:absolute;left:12px;top:-60px;z-index:50;background:#fff;border:2px solid #286a46;border-radius:9px;padding:9px 12px;font-weight:900;text-decoration:none}.skiplink:focus{top:10px}
.small{font-size:13px;color:var(--muted)}h1{margin:0}h2{font-size:18px;margin:0 0 8px}h3{font-size:15px;margin:0 0 6px}ul{padding-left:20px;margin:6px 0}
.card{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:18px;margin:12px 0;scroll-margin-top:18px}
.detailnav{display:flex;justify-content:space-between;align-items:center;margin:0 0 14px;padding:4px 2px 12px;border-bottom:1px solid var(--line);font-size:13px}.detailnav a{display:inline-flex;align-items:center;min-height:44px;font-weight:850;text-decoration:none;color:var(--forest)}.detailnav span{color:var(--muted)}
.planthead{padding:6px 2px 10px}.planthead h1{font-size:clamp(30px,6vw,44px);letter-spacing:-.04em;line-height:1.15}.scientific{color:var(--muted);font-size:15px;margin-top:2px}.aliases{font-size:12px;color:var(--muted);margin-top:4px}
.green{background:var(--green)}.yellow{background:var(--yellow)}.hold{background:var(--hold)}.danger{background:var(--danger);border-color:#e8bcbc}
.decision{border-width:2px;padding:20px 22px}.decisionlabel{font-size:12px;font-weight:800;color:var(--muted);margin-bottom:6px}
.verdictline{display:flex;align-items:center;gap:12px;flex-wrap:wrap}.gradeletter{display:inline-flex;align-items:center;justify-content:center;min-width:48px;height:48px;padding:0 10px;border-radius:12px;background:#fff;border:2px solid rgba(0,0,0,.14);font-size:26px;font-weight:950}.hold .gradeletter{font-size:17px}
.verdict{font-weight:950;font-size:clamp(22px,4.6vw,30px);line-height:1.2}.meaning{font-size:16px;font-weight:750;margin:10px 0 0}
.decisionwhy{font-size:15px;line-height:1.7;margin:10px 0 0;color:#2c3a31}.decisionwhy b{display:block;font-size:12px;color:var(--muted)}
.gradekey{display:flex;flex-wrap:wrap;gap:4px 10px;margin-top:11px;padding-top:8px;border-top:1px solid rgba(0,0,0,.08);font-size:11px;color:var(--muted)}.gradekey b{color:var(--text)}.gradekey .on{color:var(--text);font-weight:850}
.practicalgrid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.practicalgrid>div{border:1px solid var(--line);border-radius:12px;padding:12px 14px;background:#fbfdfb}.practicalgrid b{font-size:12px;color:var(--forest)}.practicalgrid p{margin:4px 0 0;font-size:14px}
.species-specific{background:#fbfcfb;padding:14px 18px}.species-specific h2{font-size:15px}.speciesexception{border-top:1px solid var(--line);padding:9px 0 0;margin-top:9px}.speciesexception>div{display:flex;justify-content:space-between;gap:12px;align-items:center;font-size:14px}.speciesexception>div span{flex:0 0 auto;font-size:12px;font-weight:800;color:var(--forest)}.speciesexception p{margin:4px 0 0;font-size:13px;color:var(--muted)}
.scopefold{margin-top:2px}.scopefold>summary{cursor:pointer;min-height:44px;font-weight:850;color:var(--forest);padding:9px 2px;list-style-position:inside;border-radius:8px}.scopefold>summary:focus-visible{outline:3px solid rgba(40,106,70,.28);outline-offset:3px}.scopebody{padding-top:4px}.scopebody>div{padding:12px 0;border-top:1px solid var(--line)}.scopebody>div:first-of-type{border-top:0;padding-top:4px}.scopecard p{margin:4px 0 0;font-size:14px}
.identity-alert{background:#fff8e6;border:1px solid #e8cf86;border-left:5px solid #a07b16;border-radius:12px;padding:12px 14px!important;margin:6px 0}.identity-alert h3{color:#6d5207}
.identity-note h3{color:#405047}.identity-note p{color:var(--muted)}
.plantphoto{display:flex;gap:12px;align-items:flex-start;margin-top:8px}.plantphoto img{width:112px;height:112px;object-fit:cover;border-radius:10px;border:1px solid var(--line);background:#fff}.plantphoto figcaption{font-size:11px;color:var(--muted);line-height:1.5}
.principles{font-size:12px;color:var(--muted);margin-top:8px}
.evidence-deep{margin-top:24px;border-top:3px solid #315f46}.sectioneyebrow{font-size:11px;font-weight:900;letter-spacing:.08em;color:#357653;margin-bottom:3px}
.evsummary{display:flex;flex-wrap:wrap;gap:6px;margin:8px 0}.evsummary span{border:1px solid var(--line);border-radius:999px;padding:4px 10px;font-size:12px;background:#f7faf7}
.legend{font-size:12px;color:var(--muted);margin:6px 0 10px}.legend b{color:var(--text)}
.evcard{border:1px solid var(--line);border-radius:12px;padding:12px 14px;margin:10px 0;background:#fff}.evhead{display:flex;flex-wrap:wrap;gap:6px;align-items:center}.evhead span{font-size:11px;font-weight:850;border:1px solid var(--line);border-radius:999px;padding:3px 8px;background:#f3f7f3}.evhead .paper{background:#eaf2fb;border-color:#c9daee}
.evcard h3{font-size:15px;margin:8px 0 6px}.evmeta{display:grid;grid-template-columns:auto 1fr;gap:2px 10px;font-size:12px;margin:0 0 8px}.evmeta dt{color:var(--muted)}.evmeta dd{margin:0}
.evcard p{font-size:13px;margin:6px 0}.evcard .limit{background:#fff8e8;border-radius:8px;padding:8px 10px}.evcard .ids{font-size:12px;color:var(--muted)}
.conflict{border:2px solid #a56b19;background:#fff5df;border-radius:12px;padding:12px;margin:10px 0}
.nutgrid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px}.nutgrid>div{border:1px solid var(--line);border-radius:10px;padding:9px;background:#fafcf9}.nutgrid b{display:block;font-size:12px;color:var(--muted)}.nutgrid strong{display:block;font-size:17px}
.relatedgrid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}.related{display:flex;align-items:center;min-height:44px;border:1px solid var(--line);border-radius:10px;padding:10px;text-decoration:none;font-weight:800;background:#fff;font-size:14px}
.share{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}.share button,.share a{border:0;border-radius:12px;padding:11px 14px;font-weight:800;background:#e7f5eb;text-decoration:none;cursor:pointer;font-size:14px}
.topmeta{display:flex;justify-content:flex-end}.langswitch{display:inline-flex;border:1px solid var(--line);border-radius:10px;overflow:hidden;background:#fff}.langswitch button{padding:6px 9px;border:0;border-radius:0;background:#fff;color:var(--muted);font-size:11px}.langswitch button.active{background:#286a46;color:#fff}
@media(max-width:700px){body{padding:12px 14px 32px}.nutgrid{grid-template-columns:1fr 1fr}.relatedgrid{grid-template-columns:1fr 1fr}}
@media(max-width:520px){.detailnav span{display:none}.planthead{padding:2px 2px 6px}.decision{padding:14px 15px}.gradeletter{min-width:40px;height:40px;font-size:21px}.meaning{font-size:15px;margin-top:8px}.decisionwhy{font-size:14px;margin-top:7px}.gradekey{gap:3px 8px;margin-top:9px;padding-top:7px;font-size:10px}.card{padding:14px}.practicalgrid,.relatedgrid{grid-template-columns:1fr}.speciesexception>div{align-items:flex-start;flex-direction:column;gap:2px}.evidence-deep{padding:13px}.evsummary{gap:5px}.evcard{padding:11px 12px;margin:8px 0}.evhead{gap:4px}.evhead span{font-size:10px;padding:2px 6px}.evcard h3{font-size:14px;line-height:1.45}.evrole{font-size:12px;line-height:1.5}.evmeta{grid-template-columns:72px 1fr;font-size:11px;gap:2px 7px}.evcard p{font-size:12px;line-height:1.55}.sourceopen{min-height:44px;align-items:center}}
'''.replace("\n","")

for p in plants:
    pid=p["id"]; d=ROOT/"plant"/pid; d.mkdir(parents=True,exist_ok=True); ko=p.get("ko") or pid; sci=p.get("scientific") or "학명 검증 중"
    title=f"육지거북 {ko} 먹어도 될까? 급여 판정·근거 | 거북밥 DB"; desc=f"육지거북에게 {ko}를 먹여도 되는지 확인한다. {ko}의 급여 판정, 학명·식물동정, 적용 범위, 주의사항과 근거를 한 페이지에서 확인한다."; canonical=f"{SITE_URL}/plant/{pid}/"
    rows=assessments_by_plant.get(pid,[])
    a=representative(rows); g=display(a)
    tone,grade,label,meaning=g["tone"],g["grade"],g["label"],g["meaning"]
    summary=(a or {}).get("why") or ("지중해 Testudo 또는 육지거북 일반을 대상으로 한 공개 판정이 아직 없다. 아래 종별 특이사항은 해당 종에만 적용된다." if not a else "근거 검토 중이다.")
    r=retail_by_id.get(pid); aliases=[]
    if r: aliases=list(dict.fromkeys((r.get("retail_terms") or [])+(r.get("aliases") or [])))
    if not aliases: aliases=list(p.get("aliases") or [])[:4]
    aliases=[x for x in aliases if x!=ko]
    # Identity risk comes only from existing data: retail name mapping or master identity status.
    identity_warning=bool((r and r.get("mapping_status")=="name_candidate_only") or p.get("identity_status")=="needs_species_level_mapping")
    role=(a or {}).get("role"); limits=(a or {}).get("limits") or []
    linked_evidence=[evidence_by_id[eid] for eid in ((a or {}).get("evidence_ids") or []) if eid in evidence_by_id]
    direct_count=sum(1 for e in linked_evidence if e.get("directness")=="direct")
    husbandry_count=sum(1 for e in linked_evidence if e.get("directness")=="expert_husbandry")
    indirect_count=len(linked_evidence)-direct_count-husbandry_count
    part_note=" / ".join(sorted({part_state_display(e.get("plant_part_state")) for e in linked_evidence if e.get("plant_part_state")})) or "근거 자료에 부위 정보가 명시되지 않음"
    en_pending=("This plant has a reviewed evidence record. The feeding grade is limited to the evidence scope shown below; it does not imply unlimited feeding." if a else "Evidence review is incomplete. Do not infer safety or unlimited feeding from missing evidence.")
    en_scope=("Reviewed evidence is available. Check source taxon, plant part, directness, and limitations below before applying the result." if a else "Evidence is incomplete; do not transfer safety assumptions across taxa.")
    en_identity="Database names are search references. Confirm the actual plant identity and contamination status before feeding."
    basis=scope_label(a)

    # 1) Decision: name → grade → meaning → why. Nothing else competes with it.
    gradekey="".join(f'<span class="{"on" if grade==x else ""}"><b>{x}</b> {y}</span>' for x,y in (("A","혼합식 활용"),("B","제한적 혼합"),("C","가끔 보조"),("D","급여 제외")))
    decision_html=f'''<section class="card {tone} decision" data-grade="{esc(grade)}" data-verdict="{esc((a or {}).get("verdict") or "none")}" aria-label="급여 판정 · {esc(grade)} {esc(label)}"><div class="decisionlabel">급여 판정 · {esc(basis)}</div><div class="verdictline"><span class="gradeletter" aria-hidden="true">{esc(grade)}</span><div class="verdict">{esc(grade+" · "+label if grade in "ABCD" else label)}</div></div><p class="meaning">{esc(meaning)}</p><p class="decisionwhy ko-evidence"><b>왜 이렇게 판정했나</b>{esc(summary)}</p><p class="en-evidence" hidden>{esc(en_pending)}</p><div class="gradekey" aria-label="급여 등급 안내">{gradekey}</div></section>'''

    # 2) Practical reading (only when there is a representative assessment).
    practical_html=(f'''<section class="card practical"><h2>급여할 때 확인할 핵심</h2><div class="practicalgrid"><div><b>식단에서의 역할</b><p>{esc(role or "현재 근거 범위 안에서 보조적으로 해석한다.")}</p></div><div><b>근거가 확인한 부위·상태</b><p>{esc(part_note)}</p></div></div></section>''' if a else "")

    # 3) Species-specific notes: visually subordinate; they never replace the default verdict.
    species_rows=[]
    for x in species_notes(rows,a):
        xg=display(x)
        who=x.get("display_group") or x.get("species_group") or x.get("animal_taxon")
        species_rows.append(f'<article class="speciesexception"><div><b>{esc(who)} <i class="small">{esc(x.get("animal_taxon"))}</i></b><span>{esc(xg["grade"]+" · "+xg["label"])}</span></div><p>{esc(x.get("why") or x.get("role") or "해당 종에 대한 별도 판정 근거가 있다.")}</p></article>')
    species_specific_html=(f'<section class="card species-specific"><h2>종별 특이사항</h2><p class="small">특정 종에서만 확인된 근거다. 위의 기본 판정을 바꾸지 않으며, 다른 육지거북 종에도 같다고 가정하지 않는다.</p>{"".join(species_rows)}</section>' if species_rows else "")

    # 4) Scope → identity → limits, stated once in one card; canonical assessment copy is rendered verbatim.
    scope=(a or {}).get("applicability_note") or {"지중해 Testudo 근거":"지중해 육지거북류(Testudo속)에 관한 근거다. 특정 종·아종을 직접 시험한 정량 자료와는 다르다.","육지거북 일반 근거":"육지거북 일반 근거를 지중해 Testudo에 적용한 판정이다. 지중해 Testudo 종 직접 판정이 아니다.","초식 파충류 일반 근거":"초식 파충류 일반 근거다. 지중해 Testudo 직접 판정이 아니다."}.get(basis,"현재 공개 근거만으로 특정 종까지 좁혀 판단하지 않는다.")
    img=image_by_plant.get(pid)
    photo_html=(f'''<figure class="plantphoto"><img src="{esc(img["image_url"])}" alt="{esc(ko)} ({esc(sci)}) 참고 이미지" loading="lazy" width="112" height="112"><figcaption>정확한 종으로 검증된 참고 이미지<br>사진: <a href="{esc(img["source_url"])}" target="_blank" rel="noopener noreferrer">{esc(img.get("creator"))}</a> · <a href="{esc(img.get("license_url"))}" target="_blank" rel="noopener noreferrer">{esc(img.get("license"))}</a><br>사진만으로 식물 종을 확정하지 않는다.</figcaption></figure>''' if img else "")
    cur=curated_identity.get(pid)
    if identity_warning:
        identity_text="한국 유통명은 검색 후보일 뿐 실제 식물의 종 동정 결과가 아니다. 상품·재배품·야생채집물은 학명을 따로 확인한다."
        cur_html=(f'<p><b>{rich(cur["headline"])}</b></p><ul>{"".join(f"<li>{rich(x)}</li>" for x in cur.get("items",[]))}</ul>' if cur else "")
        identity_html=f'''<div class="identity-alert" data-identity="alert"><h3>⚠ 식물동정 주의</h3><p class="ko-evidence">{esc(identity_text)}</p><p class="en-evidence" hidden>{esc(en_identity)}</p>{cur_html}{photo_html}</div>'''
    else:
        identity_text="이름과 학명은 검색 기준이다. 실제 급여할 식물의 종과 농약·오염 여부는 따로 확인한다."
        identity_html=f'''<div class="identity-note" data-identity="note"><h3>식물동정 확인</h3><p class="ko-evidence">{esc(identity_text)}</p><p class="en-evidence" hidden>{esc(en_identity)}</p>{photo_html}</div>'''
    limits_html="".join(f"<li>{esc(x)}</li>" for x in limits) or "<li>근거 부족 상태에서는 안전하다고 추정하지 않는다.</li><li>단독·무제한 급여 판정으로 해석하지 않는다.</li>"
    scope_html=f'''<section class="card scopecard" id="scope"><h2>판정 범위와 주의사항</h2>{identity_html if identity_warning else ""}<details class="scopefold"><summary>판정의 적용 범위와 확인되지 않은 내용 보기</summary><div class="scopebody"><div><h3>적용 범위</h3><p>{esc(scope)}</p></div>{"" if identity_warning else identity_html}<div><h3>근거로 확인되지 않은 것</h3><div class="ko-evidence"><ul>{limits_html}</ul></div><p class="en-evidence" hidden>{esc(en_scope)}</p><p class="principles">급여량·빈도·장기 안전성은 확인된 근거 범위를 넘어 정하지 않는다. 야생 섭식 기록 ≠ 무제한 급여 · 사람용 영양자료 ≠ 육지거북 독성 한계치 · 근거 부족 ≠ 안전.</p></div></div></details></section>'''

    # 5) Deep evidence: papers first, then specialist sources; each item says what it supports and what it cannot.
    ordered=sorted(linked_evidence,key=lambda e:source_kind(e)[0])
    evidence_cards=[]
    for e in ordered:
        url=e.get("url") or (f'https://doi.org/{e["doi"]}' if e.get("doi") else (f'https://pubmed.ncbi.nlm.nih.gov/{e["pmid"]}/' if e.get("pmid") else ""))
        title_raw=str(e.get("source_title") or e.get("id"))
        # Source titles can contain specialist verdict terminology; localize those labels on the Korean page.
        for raw,label in (
            ("Feed in Moderation","제한 급여"),
            ("Feed Sparingly","소량·드물게 급여"),
            ("Do not Feed","급여하지 않음"),
            ("Safe to Feed","급여 가능"),
        ):
            title_raw=title_raw.replace(raw,label)
        title_html=esc(title_raw)
        source_link=f'<a class="sourceopen" href="{esc(url)}" target="_blank" rel="noopener noreferrer" aria-label="{title_html} 원문 보기 (새 창)">원문 보기 <span aria-hidden="true">↗</span><span class="sr-only"> (새 창)</span></a>' if url else ""
        rank,kind=source_kind(e)
        ids=" · ".join(x for x in ((f'DOI {esc(e["doi"])}' if e.get("doi") else ""),(f'PMID {esc(e["pmid"])}' if e.get("pmid") else ""),(esc(e.get("year")) if e.get("year") else "")) if x)
        evidence_cards.append(f'''<article class="evcard"><div class="evhead"><span class="{'paper' if rank==0 else ''}">{kind}</span><span>{esc(directness_ko.get(e.get("directness"),e.get("directness")))}</span><span>{esc(applicability_ko.get(e.get("applicability"),e.get("applicability")))}</span></div><h3>{title_html}</h3><p class="evrole"><b>이 자료의 역할</b> · {esc(evidence_role(e))}</p><dl class="evmeta"><dt>대상 동물</dt><dd>{esc(animal_taxon_display(e.get("animal_taxon")))}</dd><dt>식물</dt><dd><i>{esc(plant_taxon_display(e.get("plant_taxon")))}</i></dd><dt>부위·상태</dt><dd>{esc(part_state_display(e.get("plant_part_state")))}</dd></dl><p><b>이 근거가 지지하는 내용</b><br>{esc(evidence_support_display(e.get("supports")))}</p><p class="limit"><b>이 근거만으로 말할 수 없는 내용</b><br>{esc(evidence_limit_display(e.get("does_not_support")))}</p>{f'<p class="ids">{ids}</p>' if ids else ''}{source_link}</article>''')
    evidence_cards_html="".join(evidence_cards) or '<p>현재 공개 가능한 개별 근거 레코드가 연결되지 않았다. 따라서 안전성을 추정하지 않는다.</p>'
    papers=sum(1 for e in linked_evidence if source_kind(e)[0]==0)
    summary_chips=f'<div class="evsummary" aria-label="연결된 근거 자료 현황"><span>연결 근거 {len(linked_evidence)}건</span><span>동료심사 논문 {papers}</span><span>직접 {direct_count}</span><span>전문 사육 {husbandry_count}</span><span>간접·맥락 {indirect_count}</span></div><p class="evcountnote">자료 건수는 연결된 출처의 현황이며, 숫자가 많다고 판정의 신뢰도나 안전성이 더 높다는 뜻은 아니다.</p>'

    # Wild feeding records (one place: static wild data + direct Ibera observations).
    wild=wild_by_plant.get(pid,[]); risk=risk_by_plant.get(pid); ib=ibera_by_plant.get(pid,[])
    conflict_html=""
    if wild and risk and (risk.get("signals") or risk.get("publication_blocker")):
        risk_items="".join(f"<li><b>{esc(x.get('type') or '위험 신호')}</b> — {esc(x.get('finding'))}<br><span class=\"small\">{esc(x.get('interpretation'))}</span></li>" for x in risk.get("signals",[]))
        conflict_html=f'''<div class="conflict"><b>⚠ 근거 충돌 또는 안전성 미해결</b><p>야생 섭식 기록이 있지만 독성·항영양성분 또는 다른 동물의 수의학적 위험 신호도 확인됐다. 야생에서 먹는다는 사실만으로 사육 급여 안전성을 확정하지 않는다.</p><ul>{risk_items}</ul><p><b>현재 공개판정의 걸림돌:</b> {esc(risk.get("publication_blocker") or "추가 검토 필요")}</p></div>'''
    wild_cards=[]
    for w in wild:
        wild_cards.append(f'''<article class="evcard wildcard"><div class="evhead"><span>야생 섭식 기록</span><span>{esc(w.get("ibera_applicability") or "적용범위 확인 필요")}</span></div><h3>{esc(w.get("tortoise_taxon") or "대상 거북 미상")} · {esc(w.get("population_region") or "지역 미상")}</h3><dl class="evmeta"><dt>확인 방법</dt><dd>{esc(w.get("study_method") or "미상")}</dd><dt>먹은 부위</dt><dd>{esc(w.get("plant_part") or "미상")}</dd><dt>시기</dt><dd>{esc(w.get("season") or "미상")}</dd><dt>섭식 기록</dt><dd>{esc(w.get("feeding_signal") or "확인")}</dd></dl><p class="limit"><b>이 기록만으로 말할 수 없는 것</b><br>{esc(w.get("limitations") or "야생 섭식 기록만으로 사육 급여량이나 무제한 급여 안전성을 정할 수 없다.")}</p><p class="ids">원자료 식물명 <i>{esc(w.get("plant_taxon_reported"))}</i> · 현재 수용명 <i>{esc(w.get("plant_taxon_accepted"))}</i> · {esc(w.get("source_id"))}</p></article>''')
    for o in ib:
        s=ibera_sources.get(o.get("source_id"),{})
        scope_txt="식물 종까지 일치" if o.get("identity_scope")=="exact_species" else "속 수준 관찰 — 이 식물의 정확한 종을 먹었다는 뜻으로 확대하지 않는다"
        link=f'<a href="{esc(s.get("url"))}" target="_blank" rel="noopener noreferrer">원 연구 확인</a>' if s.get("url") else ""
        wild_cards.append(f'''<article class="evcard wildcard" data-ibera-direct><div class="evhead"><span>이베라 야생 직접 관찰</span><span>{esc(scope_txt)}</span></div><h3><i>{esc(o.get("source_plant"))}</i> · {esc(s.get("location") or "지역 확인 필요")}</h3><dl class="evmeta"><dt>대상</dt><dd><i>{esc(s.get("taxon") or "Testudo graeca ibera")}</i></dd><dt>기간</dt><dd>{esc(s.get("study_period") or "확인 필요")}</dd><dt>섭식 부위</dt><dd>{esc(part_state_display(o.get("observed_part")) or "확인 필요")}</dd></dl><p class="ids">{esc(s.get("citation"))} {link}</p></article>''')
    wild_section=(f'''<h3 style="margin-top:18px">야생에서는 실제로 어떻게 먹었나?</h3><p class="small">야생에서 먹었다는 사실은 중요한 근거지만, 사육 급여 비율·매일 급여·무제한 안전성을 뜻하지 않는다.</p>{conflict_html}{"".join(wild_cards)}''' if wild_cards else "")

    deep_html=f'''<section class="card evidence-deep" id="evidence"><div class="sectioneyebrow">더 깊이 보기</div><h2>판정 근거 자세히 보기</h2><p class="ko-evidence small">각 자료가 <b>무엇을 지지하는지</b>와 <b>어디까지 말할 수 있는지</b>를 구분해 보여준다.<br><b>직접 근거</b>는 해당 육지거북·식물·질문을 직접 다룬 자료다. <b>간접 근거</b>는 다른 동물이나 근연 식물의 참고 자료이며, 이것만으로 급여 안전성을 확정하지 않는다.</p><p class="en-evidence" hidden>This section explains the evidence behind the conclusion. <b>Direct evidence</b> addresses the target question directly. <b>Indirect evidence</b> comes from other animals or related plants and is used only as context; indirect evidence alone does not establish safety.</p>{summary_chips}<p class="legend"><b>읽는 법</b> · 동료심사 논문과 전문 사육자료는 같은 수준의 근거가 아니다 · 성분 근거는 성분 존재만 보여줄 뿐 급여 안전성을 증명하지 않는다.</p>{evidence_cards_html}{wild_section}</section>'''

    nu=nutrition_by_id.get(pid)
    if nu:
        def nv(key,unit=""):
            v=nu.get(key)
            return "미확인" if v is None else f"{v}{unit}"
        nutrition_body=f'''<div class="nutgrid"><div><b>수분</b><strong>{nv("water_g"," g")}</strong></div><div><b>식이섬유</b><strong>{nv("fiber_g"," g")}</strong></div><div><b>칼슘</b><strong>{nv("calcium_mg"," mg")}</strong></div><div><b>인</b><strong>{nv("phosphorus_mg"," mg")}</strong></div><div><b>Ca:P</b><strong>{nv("calcium_phosphorus_ratio")}</strong></div><div><b>단백질</b><strong>{nv("protein_g"," g")}</strong></div><div><b>칼륨</b><strong>{nv("potassium_mg"," mg")}</strong></div><div><b>비타민 C</b><strong>{nv("vitamin_c_mg"," mg")}</strong></div></div><p class="small">100 g 기준 · {esc(nu.get("basis"))} · {esc(nu.get("food_description"))} · 원자료 <a href="{esc(nu.get("source_url"))}" target="_blank" rel="noopener noreferrer">{esc(nu.get("source_name"))} {esc(nu.get("source_id"))}</a></p>'''
    else:
        nutrition_body='<p class="small">검증된 공식 영양성분 자료가 아직 연결되지 않았다. 자료 부재를 0으로 처리하거나 안전·위험 판정의 근거로 쓰지 않는다.</p>'
    nutrition_html=f'''<section class="card" id="nutrition"><h2>영양성분은 참고자료로 확인하세요</h2><p class="small">사람용 식품성분 자료다. Ca:P·섬유질 등 수치는 독성·항영양성분·식물동정·대상종 근거를 대신하지 않으며, 이 수치만으로 급여 등급을 바꾸지 않는다.</p>{nutrition_body}</section>'''

    related_html="".join(f'<a class="related" href="../{esc(x["id"])}/">{esc(x.get("ko") or x["id"])} →</a>' for x in related_for(p))
    footer_html=f'''<section class="card"><h2>다른 식물도 확인하기</h2><div class="relatedgrid">{related_html}</div><p class="small">같은 과·카테고리로 묶은 탐색 링크다. 식물학적 유사성이 동일한 급여 안전성·영양가·권장도를 뜻하지 않는다.</p><div class="share"><button type="button" onclick="navigator.clipboard.writeText(location.href).then(()=>this.textContent='링크 복사 완료')">링크 복사</button><a href="../../index.html">다른 먹이 검색 →</a></div></section>'''

    alias_html=f'<div class="aliases">다른 이름 · {esc(", ".join(aliases[:6]))}</div>' if aliases else ""
    schema=json.dumps({"@context":"https://schema.org","@type":"WebPage","name":title,"description":desc,"url":canonical,"inLanguage":"ko","isPartOf":{"@type":"WebSite","name":"거북밥 DB Korea","url":SITE_URL+"/"}},ensure_ascii=False,separators=(",",":"))
    doc=f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="index,follow">
<title>{esc(title)}</title><meta name="description" content="{esc(desc)}"><link rel="canonical" href="{canonical}"><meta property="og:type" content="article"><meta property="og:locale" content="ko_KR"><meta property="og:site_name" content="거북밥 DB Korea"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{canonical}"><meta name="twitter:card" content="summary"><meta name="twitter:title" content="{esc(title)}"><meta name="twitter:description" content="{esc(desc)}">
<script type="application/ld+json">{schema}</script>
<style>{CSS}</style></head><body>
<a class="skiplink" href="#main-content">본문으로 바로가기</a><header class="detailnav"><a href="../../index.html">← 다른 식물 검색</a><div class="topmeta"><span>거북밥 · 근거 기반 판정</span></div></header><main id="main-content" tabindex="-1" data-plant-id="{esc(pid)}"><div class="planthead"><h1>{esc(ko)}</h1><div class="scientific"><i>{esc(sci)}</i></div>{alias_html}</div>{decision_html}{practical_html}{species_specific_html}{scope_html}{deep_html}{nutrition_html}{footer_html}<nav class="small" aria-label="breadcrumb"><a href="../../index.html">거북밥 DB</a> › {esc(ko)}</nav></main><script src="../../language-toggle.js?v=20260926-3" defer></script></body></html>'''
    # Final Korean morphology guard for legacy mixed-language evidence strings.\n    doc=doc.replace("급여하지 않음로", "급여하지 않음으로").replace("제한 급여으로", "제한 급여로")\n    (d/"index.html").write_text(doc,encoding="utf-8")

# Keep search-engine discovery synchronized with the same reviewed/public set
# used to generate detail pages. Preserve durable non-plant landing/guide URLs.
sitemap_path=ROOT/"sitemap.xml"
existing=sitemap_path.read_text(encoding="utf-8") if sitemap_path.exists() else ""
nonplant_urls=[]
for loc in re.findall(r"<loc>(.*?)</loc>",existing):
    if "/plant/" not in loc and loc not in nonplant_urls:
        nonplant_urls.append(loc)
if SITE_URL+"/" not in nonplant_urls:
    nonplant_urls.insert(0,SITE_URL+"/")
plant_urls=[f"{SITE_URL}/plant/{p['id']}/" for p in plants]
urls=nonplant_urls+plant_urls
sitemap_lines=['<?xml version="1.0" encoding="UTF-8"?>','<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
sitemap_lines.extend(f"  <url><loc>{esc(url)}</loc></url>" for url in urls)
sitemap_lines.append("</urlset>")
sitemap_path.write_text("\n".join(sitemap_lines)+"\n",encoding="utf-8")
print("generated",len(plants),"reviewed/public plant detail pages from",len(all_plants),"master records and",len(assessments),"assessments; sitemap plant URLs",len(plant_urls))
