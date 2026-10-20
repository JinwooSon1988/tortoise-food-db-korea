"""Build data/catalog-evidence/batch-001-20261021.json: feeding records read in open-access full texts found by the corpus search.

Every record below was checked by hand against the named table or paragraph of the full text (open-access copies fetched with fetch_europepmc.py and fetch_openalex.py, screened with extract_candidates.py).
Names are copied as printed in the source. Trinomials, misspellings and names cited second-hand next to a toxicity question are
held, not linked. Nothing here is a feeding grade, a safe-to-feed verdict, a nutrient value or a toxicity judgement.
"""
import collections, json, re, sys

OUT = sys.argv[1]
BINOM = re.compile(r"^[A-Z][a-z-]+ [a-z][a-z-]+$")

corpus = {
    "id": "corpus-2026-10-21",
    "searched": "2026-10-21",
    "searches": [
        {"service": "Europe PMC REST search (title/abstract)", "query": "TITLE_ABS:(tortoise OR tortoises OR 20 testudinid genera) AND TITLE_ABS:(diet, feeding, forage, faeces, scat, herbivory, frugivory, seed dispersal, nutrition, husbandry ...)",
         "records": 448},
        {"service": "Europe PMC REST search (full text, open access)", "query": "(tortoise OR tortoises OR 20 testudinid genera) AND (diet OR feeding OR faecal OR fecal OR scat OR forage OR eaten OR consumed) AND OPEN_ACCESS:y",
         "records": 3661},
        {"service": "OpenAlex works API", "query": "title_and_abstract.search: 20 tortoise terms x 12 diet topics, open access only", "records": 671},
    ],
    "full_texts_read_by_machine": {"europe_pmc_jats_xml": 3729, "openalex_open_access_pdf": 177,
                                   "openalex_pdf_not_downloaded": {"robots_disallow": 38, "not_pdf_or_blocked": 234}},
    "screening": "Tortoise-focused papers (tortoise term in title or abstract, beetle and butterfly homonyms excluded): 389. Machine candidates "
                 "(plant binomials in diet tables or in feeding sentences that name a tortoise): 688 in 45 papers. Each candidate paper was "
                 "then read by hand; only records confirmed in the stated table or paragraph are listed here.",
    "not_covered": "Paywalled journals, books, theses not in open repositories, keeper forums and social media. A plant with no record "
                   "here has not been shown to be safe or unsafe; it has only not been found in this corpus.",
}

sources = {
    "aissa_adel_2021": {
        "citation": "Aissa, B. H. & Adel, M. (2021) Feeding behaviour of a Testudo graeca whitei population in Mergueb Nature Reserve, Algeria. "
                    "Journal of Biodiversity Conservation and Bioresource Management 7(2)",
        "url": "https://doi.org/10.3329/jbcbm.v7i2.60150", "doi": "10.3329/jbcbm.v7i2.60150", "license": "CC BY-NC-ND (link only; text not copied)",
        "tortoise_taxon": "Testudo graeca whitei", "context": "captive", "study_id": "aissa_adel_2019_mergueb_enclosure",
        "method": {"ko": "보호구역에서 포획한 23마리(암 12, 수 8, 어린 개체 3)를 500 m 떨어진 임시 울타리(168 m²)에 두고, 보호구역에서 벤 생식물을 하루 1~2종씩 넣어 먹는지 직접 관찰 (2019년 4월, 관찰 후 방사)",
                   "en": "23 tortoises (12 F, 8 M, 3 juveniles) caught in the reserve were kept in a 168 m² enclosure 500 m away and given freshly cut reserve plants, one or two species a day, with direct observation of which were eaten (April 2019; released afterwards)"},
        "read": "publisher PDF (open access), Abstract, Methods, Table 1 (Consumed column) and Results text listing the 11 species eaten"},
    "deepak_2011": {
        "citation": "Deepak, V., Ramesh, M., Bhupathy, S. & Vasudevan, K. (2011) Indotestudo travancorica (Boulenger 1907) – Travancore Tortoise. "
                    "In: Conservation Biology of Freshwater Turtles and Tortoises. Chelonian Research Monographs 5: 054",
        "url": "https://doi.org/10.3854/crm.5.054.travancorica.v1.2011", "doi": "10.3854/crm.5.054.travancorica.v1.2011", "license": "link only; text not copied",
        "tortoise_taxon": "Indotestudo travancorica", "context": "wild", "study_id": "deepak_2011_species_account",
        "method": {"ko": "IUCN 거북 전문가 그룹 종 설명서의 야생 식성 요약 (Vijaya 1983, Ramesh & Parthasarathy 2006, Vasudevan et al. 2010 인용; 분변 32개 분석 포함). 1차 연구 원문은 이번에 읽지 않음",
                   "en": "Wild-diet summary in an IUCN Tortoise and Freshwater Turtle Specialist Group species account (citing Vijaya 1983, Ramesh & Parthasarathy 2006, Vasudevan et al. 2010, incl. 32 faecal samples). The primary studies were not read here"},
        "read": "species account PDF (iucn-tftsg.org), Natural History paragraph on diet, p. 054.4"},
    "auffenberg_weaver_1969": {
        "citation": "Auffenberg, W. & Weaver, W. G., Jr. (1969) Gopherus berlandieri in southeastern Texas. Bulletin of the Florida State Museum, Biological Sciences 13(3): 141-203",
        "url": "https://doi.org/10.58782/flmnh.stti1136", "doi": "10.58782/flmnh.stti1136", "license": "link only; text not copied",
        "tortoise_taxon": "Gopherus berlandieri", "context": "wild", "study_id": "auffenberg_weaver_1961_1967_texas",
        "method": {"ko": "미국 텍사스 남동부 캐머런 카운티 야생 개체군을 1961~1967년 간헐적으로 조사: 직접 섭식 관찰과 1966년 8월 수집 분변의 식물 조각 동정 (Table 10)",
                   "en": "Wild populations in Cameron County, SE Texas, studied intermittently 1961-1967: direct feeding observations and plant remains identified in droppings collected in August 1966 (Table 10)"},
        "read": "museum bulletin PDF (flmnhbulletin.com), Food and Feeding section and Table 10, pp. 186-188"},
    "puga_torres_2017": {
        "citation": "Puga-Torres, B. H. et al. (2017) Comparison of the effect of three food diets provided to giant tortoises (Chelonoidis guntheri and "
                    "Chelonoidis vicina) bred in captivity at Isabela Island – Galápagos. Journal of Veterinary Science & Animal Husbandry 5(2): 204",
        "url": "https://doi.org/10.15744/2348-9790.5.204", "doi": "10.15744/2348-9790.5.204", "license": "CC BY",
        "tortoise_taxon": "Chelonoidis guntheri, Chelonoidis vicina (juveniles, 2-4 years)", "context": "captive", "study_id": "puga_torres_2017_isabela_diets",
        "method": {"ko": "갈라파고스 이사벨라섬 번식센터의 2~4살 어린 개체 60마리를 20마리씩 3그룹으로 나눠 6개월간 대조 식단(오토이 단독)과 혼합 식단 A·B(B는 비타민 보충)를 주 3회 급여하고 체중·등갑 크기 비교",
                   "en": "60 juveniles (2-4 years) at the Isabela Island breeding centre, three groups of 20, fed for 6 months a control diet (otoy only) or mixed diets A and B (B with vitamin supplement) three times a week; weight and carapace size compared"},
        "read": "publisher PDF (open access), Abstract, Materials and Methods, Table 2, Results"},
    "puga_torres_2017_cited": {
        "citation": "Puga-Torres, B. H. et al. (2017), Introduction, citing Cayot (1999) and Márquez Cruz (1999)",
        "url": "https://doi.org/10.15744/2348-9790.5.204", "doi": "10.15744/2348-9790.5.204", "license": "CC BY",
        "tortoise_taxon": "Galápagos giant tortoises (Chelonoidis spp., wild)", "context": "wild", "study_id": "cayot_1999_marquez_1999_cited",
        "method": {"ko": "다른 논문의 서론이 인용한 야생 식성 문장 (Cayot 1999; Márquez Cruz 1999). 인용된 원문은 읽지 않음",
                   "en": "Wild-diet statements cited in another paper's introduction (Cayot 1999; Márquez Cruz 1999). The cited originals were not read"},
        "read": "publisher PDF, Introduction (citation only)"},
    "ellis_soto_2017": {
        "citation": "Ellis-Soto, D., Blake, S., Soultan, A., Guézou, A., Cabrera, F. & Lötters, S. (2017) Plant species dispersed by Galapagos tortoises surf the "
                    "wave of habitat suitability under anthropogenic climate change. PLoS ONE 12(7): e0181333",
        "url": "https://doi.org/10.1371/journal.pone.0181333", "doi": "10.1371/journal.pone.0181333", "license": "CC BY",
        "tortoise_taxon": None, "context": "wild", "study_id": "ellis_soto_2017_santa_cruz_dung",
        "method": {"ko": "갈라파고스 산타크루스섬 두 지역에서 고도 50 m마다 처음 만난 신선한 분변 더미를 수집(같은 개체 중복 최소화)하고 체로 걸러 종자 수를 셈",
                   "en": "On Santa Cruz Island, the first fresh dung pile met at each 50 m elevation step was collected (limiting repeats from one animal), washed and sieved, and seeds counted"},
        "read": "Europe PMC full-text XML, Methods, Results and Table 1"},
}

records, held = [], []


def rec(src, name, typ, ver, locator, part, finding, tortoise=None):
    if not BINOM.match(name):
        held.append({"source_key": src, "reported_name": name, "reason": "not a species binomial (infraspecific, hybrid or unidentified)"})
        return
    r = {"source_key": src, "reported_name": name, "type": typ, "verification": ver, "locator": locator, "plant_part": part, "finding": finding}
    if tortoise:
        r["tortoise"] = tortoise
    records.append(r)


def hold(src, name, reason):
    held.append({"source_key": src, "reported_name": name, "reason": reason})


# A. Aissa & Adel 2021, Table 1: 40 species offered, Consumed Yes/No (order and values copied from the table; 11 Yes as in the Results text)
table1 = [("Arthrophytum scoparium", 0), ("Salsola vermiculata", 0), ("Daucus sahariensis", 0), ("Ferula communis", 0), ("Thapsia garganica", 0),
          ("Anacyclus clavatus", 0), ("Anvillea radiata", 0), ("Artemisia campestris", 0), ("Artemisia herba-alba", 0), ("Atractylis cancellata", 0),
          ("Bombycilaena discolor", 0), ("Calendula arvensis", 0), ("Leontodon hispidus", 0), ("Pallenis hierichuntica", 0), ("Arnebia decumbens", 0),
          ("Echium pycnanthum", 0), ("Noea micrantha", 0), ("Eruca vesicaria", 1), ("Moricandia arvensis", 1), ("Neslia paniculata", 0),
          ("Rapistrum rugosum", 1), ("Vella pseudocytisus", 1), ("Herniaria fontanesii", 0), ("Lomelosia stellata", 0), ("Retama retam", 0),
          ("Vicia lutea", 1), ("Vicia monantha monantha", 1), ("Ajuga iva", 1), ("Marrubium supinum", 0), ("Malva parviflora", 1),
          ("Peganum harmala", 0), ("Phelipanche mutelii", 1), ("Glaucium corniculatum", 0), ("Reseda lutea lutea", 1), ("Andropogon distachyos", 0),
          ("Cympobogon schoenanthus", 0), ("Hordeum vulgare", 1), ("Lygeum spartum", 0), ("Stipa tenacissima", 0), ("Stipellula parviflora", 0)]
assert len(table1) == 40 and sum(v for _, v in table1) == 11
for name, eaten in table1:
    if name == "Cympobogon schoenanthus":
        hold("aissa_adel_2021", name, "misspelt genus in the source (Cymbopogon?); not linked by guesswork")
        continue
    if eaten:
        rec("aissa_adel_2021", name, "captive_feeding_record", "full_text_verified", "Table 1 (Consumed: Yes); Results", None,
            {"ko": "보호구역에서 벤 생식물을 울타리 안 거북에게 주었을 때 먹음 — 제공한 40종 중 먹은 11종 중 하나 (알제리 Mergueb 보호구역 개체, 2019년 4월)",
             "en": "Eaten when freshly cut from the reserve and given to the enclosed tortoises — one of 11 of 40 species offered that were eaten (Mergueb Reserve animals, Algeria, April 2019)"})
    else:
        rec("aissa_adel_2021", name, "offered_not_eaten", "full_text_verified", "Table 1 (Consumed: No)", None,
            {"ko": "2019년 4월 울타리 안 거북에게 제공했으나 먹지 않음 (이 시기·이 개체군의 관찰일 뿐 독성이나 부적합 판정이 아님)",
             "en": "Offered to the enclosed tortoises in April 2019 but not eaten (an observation for this season and population only; not a toxicity or suitability verdict)"})

# B. Deepak et al. 2011 species account, diet paragraph
leaves = {"ko": "잎", "en": "leaves"}
for name in ["Synedrella nodiflora", "Desmodium repandum", "Senecio scandens", "Mimosa pudica"]:
    rec("deepak_2011", name, "wild_feeding_observation", "review_full_text_verified", "Natural History (diet), p. 054.4", leaves,
        {"ko": "야생 트라방코르육지거북이 먹는 초본의 잎으로 종 설명서에 기재됨 (인도 서고츠)", "en": "Listed in the species account as a herb whose leaves wild Travancore tortoises eat (Western Ghats, India)"})
rec("deepak_2011", "Ficus virens", "wild_feeding_observation", "review_full_text_verified", "Natural History (diet), p. 054.4", {"ko": "떨어진 열매", "en": "fallen fruit"},
    {"ko": "야생 트라방코르육지거북이 떨어진 열매를 먹는다고 종 설명서에 기재됨 (인도 서고츠)", "en": "Listed in the species account as a fallen fruit wild Travancore tortoises eat (Western Ghats, India)"})
rec("deepak_2011", "Dillenia pentagyna", "wild_feeding_observation", "review_full_text_verified", "Natural History (diet), p. 054.4",
    {"ko": "떨어진 열매 (분변에서 종자 확인)", "en": "fallen fruit (seeds found in faeces)"},
    {"ko": "야생 트라방코르육지거북이 떨어진 열매를 먹고, 분변 32개 분석에서 종자가 나온 식물로 종 설명서에 기재됨 (인도 서고츠)",
     "en": "Listed in the species account as a fallen fruit eaten by wild Travancore tortoises, with seeds found in an analysis of 32 faecal samples (Western Ghats, India)"})
hold("deepak_2011", "Grewia tilaefolia", "spelling differs from the accepted epithet (tiliifolia); not linked by guesswork")
hold("deepak_2011", "Veronica buabaumii", "misspelt epithet in the source; not linked by guesswork")

# C. Auffenberg & Weaver 1969, Food and Feeding, Table 10
rec("auffenberg_weaver_1969", "Opuntia lindheimeri", "wild_feeding_observation", "full_text_verified", "Food and Feeding, pp. 186-188; Table 10",
    {"ko": "줄기 마디(패드), 열매, 꽃", "en": "pads, fruits, flowers"},
    {"ko": "야생 베를란디에리고퍼거북이 가장 흔히 먹는 식물로 직접 관찰됨 (여름에 늘고 봄에는 풀이 주식); 분변에서도 잎·열매 조각 확인. 원문에는 사육 중 죽은 1마리의 소장이 가시가 남은 작은 패드로 막혀 있었다는 기록도 있음 (미국 텍사스 남동부, 1961~1967년)",
     "en": "Directly observed as the plant wild Texas tortoises eat most often (more in summer; grass dominates in spring); leaf and fruit remains also in droppings. The source also records one captive animal that died with its small intestine blocked by a small, still-spiny pad (SE Texas, 1961-1967)"})
hold("auffenberg_weaver_1969", "Opuntia leptocaulus", "spelling differs from the published epithet (leptocaulis); not linked by guesswork")

# D. Puga-Torres et al. 2017, Table 2 (diets A and B) and the control diet
diet_finding = {"ko": "갈라파고스 이사벨라섬 번식센터의 어린 개체(2~4살)에게 6개월간 혼합 실험 식단 A·B의 재료로 급여; 대조 식단과 체중·크기 증가 차이 없음 (연구 급여 기록이며 급여 권장이나 안전성 판정이 아님)",
                "en": "Fed for 6 months as an ingredient of mixed experimental diets A and B to juveniles (2-4 years) at the Isabela Island breeding centre; growth did not differ from the control diet (a study diet record, not a recommendation or safety verdict)"}
fruit = {"ko": "열매", "en": "fruit"}
for name, part in [("Manihot esculenta", None), ("Daucus carota", None), ("Passiflora edulis", fruit), ("Psidium guajava", fruit), ("Pennisetum purpureum", None),
                   ("Citrus aurantium", fruit), ("Ananas comosus", fruit), ("Solanum tuberosum", None), ("Leucaena leucocephala", None)]:
    rec("puga_torres_2017", name, "captive_feeding_record", "full_text_verified", "Table 2; Materials and Methods", part, diet_finding)
rec("puga_torres_2017", "Musa paradisiaca", "captive_feeding_record", "full_text_verified", "Table 2; Materials and Methods",
    {"ko": "열매, 줄기와 잎", "en": "fruit, trunk and leaf"}, diet_finding)
rec("puga_torres_2017", "Xanthosoma sagittifolium", "captive_feeding_record", "full_text_verified", "Abstract; Materials and Methods; Table 2", None,
    {"ko": "이사벨라섬 번식센터의 기존 단독 식단(오토이)이자 이 연구의 대조 식단; 혼합 식단 A·B에도 포함. 6개월간 세 식단의 체중·크기 증가 차이 없음 (연구 급여 기록이며 급여 권장이나 안전성 판정이 아님)",
     "en": "The breeding centre's usual single-food diet (otoy) and the study's control diet; also in mixed diets A and B. Growth did not differ among the three diets over 6 months (a study diet record, not a recommendation or safety verdict)"})
hold("puga_torres_2017", "Spondias movii", "epithet not a published name as printed; not linked by guesswork")
hold("puga_torres_2017", "Brassica oleacea", "misspelt epithet in the source (oleracea?); not linked by guesswork")
hold("puga_torres_2017", "Pennisetum purpureum híbrido", "hybrid cultivar, not a species")
for name in ["Opuntia echios", "Azolla microphylla", "Psidium galapageium"]:
    rec("puga_torres_2017_cited", name, "wild_feeding_observation", "literature_lead_not_reverified", "Introduction (citing Cayot 1999; Márquez Cruz 1999)", None,
        {"ko": "다른 논문 서론에서 야생 갈라파고스땅거북이 먹는 식물로 인용됨 (인용된 원문 재확인 전)", "en": "Cited in another paper's introduction as eaten by wild Galápagos tortoises (cited original not rechecked)"})
hold("puga_torres_2017_cited", "Hippomanea mancinella", "misspelt genus, cited second-hand, and a toxic-plant question that needs the primary source; not linked")
hold("puga_torres_2017_cited", "Tillandsia insulares", "spelling differs from the published epithet (insularis); not linked by guesswork")

# E. Ellis-Soto et al. 2017: seeds in dung piles, one record per tortoise species (no pooling across species)
for name, ko, en_, counts in [("Psidium guajava", "구아바", "guava", {"porteri": (71, 159), "donfaustoi": (25, 63)}),
                              ("Passiflora edulis", "패션프루트", "passion fruit", {"porteri": (67, 159), "donfaustoi": (12, 63)})]:
    for tort, area_ko, area_en in [("porteri", "La Reserva", "La Reserva"), ("donfaustoi", "Cerro Fatal", "Cerro Fatal")]:
        n, tot = counts[tort]
        rec("ellis_soto_2017", name, "wild_feeding_observation", "full_text_verified", "Results; Table 1", {"ko": "열매 (분변에서 종자 회수)", "en": "fruit (seeds recovered from dung)"},
            {"ko": f"야생 갈라파고스땅거북 분변 더미 {tot}개 중 {n}개에서 {ko} 종자 확인 (산타크루스섬 {area_ko})",
             "en": f"{en_.capitalize()} seeds in {n} of {tot} dung piles of wild Galápagos tortoises (Santa Cruz Island, {area_en})"},
            tortoise="Chelonoidis " + tort)

# Papers read by hand whose plant names are not feeding evidence (kept so the catalog can say the name was seen and rejected)
reviewed_not_feeding = [
    {"source": "Stemle et al. 2024, Ecology and Evolution, doi:10.1002/ece3.70509 (PMC11532232), Table A5", "reason": "nitrogen of the three most abundant plants near burrows; not plants seen eaten",
     "names": ["Aristida stricta", "Melinis repens", "Sporobolus indicus", "Erigeron canadensis", "Galactia elliottii", "Galactia regularis", "Geobalanus oblongifolius",
               "Grona triflora", "Imperata cylindrica", "Indigofera hirsuta", "Pityopsis graminifolia", "Rhynchosia cinerea", "Chamaecrista fasciculata"]},
    {"source": "Berardo et al. 2015, Comptes Rendus Biologies, doi:10.1016/j.crvi.2015.03.002, Table 3", "reason": "habitat (vegetation type) selection, not diet", "names": ["Juniperus macrocarpa"]},
    {"source": "Puga-Torres et al. 2017, Introduction", "reason": "habitat association with tree cacti, not diet", "names": ["Opuntia galapageia"]},
    {"source": "Jennings & Berry 2015 publisher PDF text", "reason": "PDF text-extraction artefact; the name is not in the diet tables of the Europe PMC XML", "names": ["Eriogonum angulosum"]},
]

out = {"schema_version": "1.0", "batch": "batch-001", "built": "2026-10-21", "corpus": corpus,
       "scope": "Feeding records from the corpus search, read by hand in the open-access full text. Observation and study-diet records only: never a "
                "feeding grade, safe-to-feed verdict, nutrient value or toxicity judgement. Linked to a catalog entry only through an exact GBIF species "
                "match, a GBIF synonym of an accepted species, or a recorded orthographic variant; the name printed in the source is kept.",
       "verification_levels": {"full_text_verified": "the stated table or section of the original study was read and names the plant with the finding",
                               "review_full_text_verified": "read in the full text of a review or species account; the primary studies it cites were not read",
                               "literature_lead_not_reverified": "cited second-hand or abstract only; the original was not re-read"},
       "sources": [dict(source_key=k, **v) for k, v in sources.items()], "records": records, "held_not_linked": held,
       "reviewed_not_feeding_evidence": reviewed_not_feeding}
open(OUT, "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, indent=1) + "\n")
print(len(records), collections.Counter((r["source_key"], r["type"], r["verification"]) for r in records), "held", len(held))
