"""Per-source settings for the Testudo and forum/zoo-diary passes. Writes b2_config_testudo.json and b2_config_forums.json."""
import json

M = lambda ko, en: {"ko": ko, "en": en}
EX_TERMS = {"exclude": True, "exclude_reason": "site terms forbid electronic storage or processing (testudo-farm.de)"}
EX_ZOLW = {"exclude": True, "exclude_reason": "site rules (zolw.info, section 14) forbid copying or distributing posted articles in any form without the authors' consent"}
T = {
 "lagarde2003_ecography": {"exclude": True, "exclude_reason": "publisher PDF re-hosted on a keeper site; not an authorised open copy"},
 "testudo_farm_wegehaupt": EX_TERMS,
 "jia2011_azr": {"study_id": "jia_2011_huocheng_horsfieldii", "context": "wild", "tortoise_taxon": "Testudo horsfieldii (Agrionemys horsfieldii)",
  "citation": "Jia, F., Li, Z., Jin, X. & Zhang, W. (2011) Analysis on plant species composition and structure in the Testudo horsfieldi reserve, Yili, Xinjiang [贾风勤 등, 新疆伊犁四爪陆龟保护区植物组成及其结构分析]. Arid Zone Research 28(6):1020-1024, doi:10.13866/j.azr.2011.06.015",
  "url": "https://doi.org/10.13866/j.azr.2011.06.015",
  "method": M("중국 신장 훠청 러시아육지거북 보호구역의 식물 65종을 거북이 먹는 빈도에 따라 즐겨 먹음·보통·가끔·먹지 않음으로 분류한 표 1 (관찰 방법은 원문에 기술되지 않음; 글꼴이 깨진 PDF라 쪽 이미지에서 옮겨 적고 텍스트층과 대조)",
              "Table 1 classes the 65 plant species of the Testudo horsfieldii reserve in Huocheng, Xinjiang, China by how often the tortoises eat them: favoured, general, occasional or not eaten (the paper does not describe how this was observed; the PDF has scrambled fonts, so the table was transcribed from the page image and checked against the text layer)"),
  "read": "free PDF on the journal site (Chinese); Table 1, p. 1022"},
 "vertebradosibericos_tgraeca": {"study_id": "andreu_1987_donana_graeca_via_mncn", "verification": "review_full_text_verified", "context": "wild",
  "citation": "Díaz-Paniagua, C. & Andreu, A. C. (2015) Tortuga mora - Testudo graeca. Ecología trófica. In: Salvador, A. & Marco, A. (eds.) Enciclopedia Virtual de los Vertebrados Españoles. Museo Nacional de Ciencias Naturales (CSIC), Madrid",
  "tortoise_taxon": "Testudo graeca",
  "method": M("스페인 국립자연과학관(MNCN-CSIC) 척추동물 백과의 식성 항목: 도냐나 야생 개체의 분변·관찰 자료(Andreu 1987)를 부위·월별로 정리한 표 1과 무르시아·마요르카 기록(López-Jurado et al. 1979 인용) (1차 연구 미확인)",
              "Diet entry of the Spanish national natural history museum's (MNCN-CSIC) vertebrate encyclopedia: Table 1 with Doñana faecal and observation data by part and month (Andreu 1987) and records from Murcia and Mallorca (citing López-Jurado et al. 1979; primary studies not read)"),
  "read": "public web page (Spanish); Tabla 1 and text"},
 "vertebradosibericos_thermanni": {"study_id": "bertolero_2015_hermanni_mncn", "verification": "review_full_text_verified", "context": "wild",
  "citation": "Bertolero, A. (2015) Tortuga mediterránea - Testudo hermanni. Ecología trófica. In: Salvador, A. & Marco, A. (eds.) Enciclopedia Virtual de los Vertebrados Españoles. MNCN-CSIC, Madrid",
  "tortoise_taxon": "Testudo hermanni",
  "method": M("스페인 국립자연과학관 척추동물 백과의 식성 항목: 에브로 삼각주·메노르카·가라프 개체군 연구 요약 (1차 연구 미확인)",
              "Diet entry of the MNCN-CSIC vertebrate encyclopedia summarising studies of the Ebro delta, Menorca and Garraf populations (primary studies not read)"),
  "read": "public web page (Spanish)"},
 "munoz2009_montsant": {"study_id": "munoz_2009_montsant_hermanni", "context": "wild", "tortoise_taxon": "Testudo hermanni hermanni",
  "type_map": {"offered_not_eaten": "wild_diet_not_detected"},
  "citation": "Muñoz, A., Soler, J. & Martínez-Silvestre, A. (2009) Aportaciones al estudio de la alimentación de Testudo hermanni hermanni en el Montsant. Boletín de la Asociación Herpetológica Española 20",
  "method": M("스페인 카탈루냐 몬산트 재도입 개체군의 분변 분석(식물 24분류군)과 관찰 기록", "Faecal analysis (24 plant taxa) and observations of the reintroduced population of Montsant, Catalonia, Spain"),
  "read": "PDF on a public site (Spanish); faecal table and Discussion"},
 "mazzotti2007_mesola": {"study_id": "mazzotti_2007_mesola_hermanni", "context": "wild", "tortoise_taxon": "Testudo hermanni",
  "citation": "Mazzotti, S. et al. (2007) La popolazione di Testudo hermanni del Bosco della Mesola. Quaderni del Museo di Storia Naturale di Ferrara",
  "method": M("이탈리아 메솔라 숲 야생 개체군의 식이 스펙트럼 표 5.3 (조사 방법·먹은 부위별 36분류군; 부위 열은 쪽 이미지에서 확인)",
              "Diet spectrum Table 5.3 of the wild population of Bosco della Mesola, Italy (36 plant taxa by method and part; the part column was read from the page image)"),
  "read": "PDF from the Ferrara natural history museum site (Italian); Tab. 5.3, p. 102"},
 "mitrevichin2023_azb": {"study_id": "mitrevichin_2023_azb_suppl16", "context": "wild", "tortoise_taxon": "Testudo graeca / Testudo hermanni (Bulgaria)",
  "method": M("불가리아 야생 개체군의 생물·생태 특성 논문 중 섭식 관찰", "Feeding observations in a paper on the biology and ecology of wild populations in Bulgaria"),
  "read": "open-access PDF (Acta Zoologica Bulgarica Suppl. 16)"},
 "hetenyi2016_mal": {"study_id": "hetenyi_2016_hermanni_intake", "context": "captive", "tortoise_taxon": "Testudo hermanni",
  "method": M("헝가리 수의대 사육 그리스거북 수컷 12마리에게 단일 먹이를 주고 건물 섭취량을 측정한 시험", "Single-food trials measuring voluntary dry-matter intake in 12 captive male Hermann's tortoises (Hungarian veterinary university)"),
  "read": "open repository PDF (Hungarian); Introduction and Table 2"},
}
F = {
 "fz_de_wegehaupt_habitat": EX_TERMS, "fz_de_testudofarm_futterpflanzen": EX_TERMS, "fz_de_testudofarm_ernaehrung": EX_TERMS, "fz_de_testudofarm_garrigue": EX_TERMS,
 "fz_ru_cherepahi_rasteniya": {"exclude": True, "exclude_reason": "translation of The Tortoise Table, whose terms forbid reuse"},
 # Terms checked 2026-10-22 (licence review): zolw.info rules section 14 bar copying or distributing posted articles in any form
 # without the authors' consent; the IGSN Impressum allows downloads and copies for private, non-commercial use only.
 "fz_pl_zolwinfo_rosliny": EX_ZOLW, "fz_pl_zolwinfo_trujace": EX_ZOLW, "fz_pl_zolwinfo_horsfieldii": EX_ZOLW,
 "fz_de_igsn_futterpflanzen": {"exclude": True, "exclude_reason": "site Impressum (schildkroeten-schutz.de) allows downloads and copies for private, non-commercial use only"},
 "fz_es_vertebrados_thermanni": {"exclude": True, "exclude_reason": "same page extracted in the Testudo pass"},
 "fz_es_vertebrados_tgraeca": {"exclude": True, "exclude_reason": "same page extracted in the Testudo pass"},
 "fz_ja_zootime": {"study_id": "zootime_2020_blog", "verification": "community_report_unverified", "context": "keeper",
  "method": M("일본 이동동물원(ZOOTIME) 대표의 블로그 글 (동물원 사육지침이 아닌 운영자 경험담으로 분류)", "Blog post by the director of a Japanese mobile zoo (ZOOTIME), classed as an operator's experience, not a zoo guideline")},
 "fz_ja_ichikawa_diary": {"study_id": "ichikawa_zoo_2026_sulcata_diary", "context": "captive",
  "method": M("일본 이치카와시 동식물원 사육일지(설카타 개체)", "Keeper diary of Ichikawa City Zoo, Japan (one sulcata)")},
 "fz_ja_nonhoi_interview": {"study_id": "nonhoi_park_sulcata_interview", "context": "captive",
  "method": M("일본 도요하시 논호이파크 사육사 인터뷰", "Keeper interview, Nonhoi Park, Toyohashi, Japan")},
 "fz_en_oglebayzoo": {"study_id": "oglebay_zoo_radiata_page", "context": "captive"},
 "fz_en_lazoo": {"study_id": "la_zoo_radiata_page", "context": "captive"},
 "fz_en_elpasozoo": {"study_id": "el_paso_zoo_radiata_page", "context": "captive"},
 "fz_de_uzh_fuetterung": {"study_id": "tierspital_zurich_feeding_sheet", "context": "captive",
  "method": M("스위스 취리히대 동물병원 보호자 안내문", "Owner information sheet of the University of Zurich animal hospital")},
 "fz_de_wettengl_futterpflanzen": {"study_id": "wettengl_2018_vet_list", "context": "captive",
  "method": M("독일 동물병원(파충류 진료) 누리집의 먹이 식물 안내", "Food plant guidance on a German veterinary practice website (reptile medicine)")},
 "fz_it_carabinieri": {"study_id": "italy_cites_2020_husbandry_guideline", "context": "captive"},
}
json.dump(T, open("b2_config_testudo.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump(F, open("b2_config_forums.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(T), len(F))
