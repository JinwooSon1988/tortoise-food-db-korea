"""Assemble b3_config.json for batch 003 from the agents' folders, the Europe PMC queue figures and hand-written settings.
Run from the scratchpad: python -X utf8 -I <this> <b3 dir> <queue dir> <out json>"""
import json, re, sys, collections
from pathlib import Path

B3, Q, OUT = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
M = lambda ko, en: {"ko": ko, "en": en}
docs, leads, classes = 0, 0, collections.Counter()
seen = set()
for d in sorted(p for p in B3.iterdir() if p.is_dir() and (p / "sources.jsonl").exists()):
    for line in (d / "sources.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            s = json.loads(line)
            k = s.get("doi") or s.get("url") or s["source_id"]
            k = k + "|" + s["source_id"] if "deserttortoise.org" in k else k  # several papers share one proceedings volume
            if k not in seen:
                seen.add(k); docs += 1; classes[s.get("source_class") or "other"] += 1
    if (d / "leads.jsonl").exists():
        leads += sum(1 for l in (d / "leads.jsonl").read_text(encoding="utf-8").splitlines() if l.strip())
qr = [json.loads(l) for l in (Q / "queue_results.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
searched, with_hits = len(qr), sum(1 for r in qr if r["hit_count"])
oa = {h["pmcid"] for r in qr for h in r["hits"] if h.get("pmcid") and h.get("isOpenAccess") == "Y"}
REVIEW, ABSTRACT = "review_full_text_verified", "abstract_checked"
TRANSCRIBED = ("OCR scan of the Desert Tortoise Council symposium proceedings (deserttortoise.org); the table rows were transcribed "
               "from the page images because the OCR text layer is garbled (two tables checked against the images)")
src = {}
# TFTSG species accounts and other compilations: the primary studies were not read.
for k in ["tftsg_crm5_028_arnoldi", "tftsg_crm5_061_hololissa", "tftsg_crm5_030_angulata", "tftsg_crm5_106_elegans", "tftsg_crm5_109_agassizii",
          "tftsg_crm5_142_berlandieri", "tftsg_crm5_086_emys", "tftsg_crm5_120_eastern_graeca", "tftsg_crm5_117_western_graeca",
          "tftsg_crm5_059_hermanni", "tftsg_crm5_122_marginata", "tftsg_crm5_070_homeana", "tftsg_crm5_084_erosa", "bailey1986_bcg_testudo",
          "joseph2024_ppp3_aldabrachelys", "falcon2018_biorxiv_chelonian_frugivory", "cortesgomez2015_univscient_table3",
          "sobralsouza2017_pecon_rewilding", "epmc_PMC11405292"]:
    src[k] = {"verification": REVIEW}
for k in ["B3-GOPH-006", "B3-GOPH-009", "B3-GOPH-010", "B3-GOPH-013", "B3-GOPH-015"]:  # proceedings abstracts
    src[k] = {"verification": ABSTRACT, "read": TRANSCRIBED}
for k in ["B3-GOPH-001", "B3-GOPH-002", "B3-GOPH-003", "B3-GOPH-004", "B3-GOPH-005", "B3-GOPH-007", "B3-GOPH-008", "B3-GOPH-014"]:
    src[k] = {"read": TRANSCRIBED}
src["lagarde2003_ecography"] = {"read": "PDF in the publication archive of the authors' institute (CNRS Centre d'Etudes Biologiques de Chize, "
                                        "cebc.cnrs.fr); batch 002 excluded only a copy re-hosted on a keeper site"}
src["B3-GOPH-011"] = {"read": TRANSCRIBED, "toxicity": {"Sapium biloculare": {
    "test_animal": M("야생 사막거북 사체 4마리의 위장 내용물과 쥐 뇌세포막을 이용한 시험관 생물검정(포볼에스터 유사 활성)",
                     "gut contents of 4 dead wild desert tortoises and an in-vitro bioassay with rat brain membranes (phorbol-ester-like activity)"),
    "conditions": M("가뭄기에 떨어진 잎·열매 등을 먹던 개체; 식물의 모든 부위에서 활성이 나왔고 4마리 중 2마리의 위장에서 이 식물이 확인됨. "
                    "저자는 폐사에 기여했을 가능성을 제시했으나 결과는 결론적이지 않다고 적음 (학회 발표 원고)",
                    "tortoises eating fallen litter during a drought; all plant parts were bioactive and the plant was found in the guts of 2 of 4 "
                    "dead tortoises; the author suggests a possible contribution to mortality but calls the results inconclusive (symposium paper)")}}}
cfg = {
    "batch": "batch-003", "built": "2026-10-22",
    "corpus": {
        "id": "corpus-2026-10-22-b3", "searched": "2026-10-22",
        "searches": [
            {"area": "Every catalog species with land-tortoise terms", "languages": ["en"],
             "services": "Europe PMC REST search; open-access full texts (JATS XML) of the hits scanned for the species name"},
            {"area": "North American tortoises (Gopherus)", "languages": ["en", "es"], "services": "web search; Desert Tortoise Council proceedings 1976-2003; repositories"},
            {"area": "IUCN/SSC TFTSG species accounts (all Testudinidae)", "languages": ["en"], "services": "iucn-tftsg.org; chelonian.org"},
            {"area": "South American and Galapagos tortoises", "languages": ["pt", "es", "en"], "services": "web search; SciELO; repositories; PMC"},
            {"area": "Madagascar, Indian Ocean, Africa and Asia (radiated tortoise priority)", "languages": ["en", "fr"], "services": "web search; HAL; open journals"},
            {"area": "Mediterranean Testudo and Russian tortoise", "languages": ["en", "fr", "tr", "ru", "zh", "es", "it"], "services": "web search; theses; BCG journal archive"},
            {"area": "Sulcata and leopard tortoises", "languages": ["en", "fr", "zh", "id"], "services": "web search; OpenAlex; university repositories"}],
        "species_searched_in_europe_pmc": searched, "species_with_europe_pmc_hits": with_hits, "open_access_full_texts_scanned": len(oa),
        "documents_read": docs, "documents_by_class": dict(classes), "leads_not_accessed": leads,
        "not_accessible": "Paywalled journals without an open copy, hosts behind bot challenges, robots.txt-disallowed paths and scanned PDFs without a text layer. Nothing was bypassed.",
        "summary": {
            "ko": ("카탈로그 식물 %d종을 Europe PMC에서 육지거북 용어와 함께 검색해 %d종에서 문헌을 찾았고, 오픈액세스 원문 %d편에서 학명이 나오는 위치를 확인했습니다. "
                   "또한 미국 사막거북 학회 발표집, IUCN 종 설명서, 남미·갈라파고스·마다가스카르·인도양·지중해·중앙아시아 연구와 학위논문 등 문서 %d건을 저장해 표와 본문을 확인했습니다. "
                   "학명이 원문에 인쇄된 기록만 연결했고, 종 설명서·리뷰를 거친 기록은 1차 연구 미확인으로 표시합니다.") % (searched, with_hits, len(oa), docs),
            "en": ("%d catalog species were searched in Europe PMC together with land-tortoise terms (hits for %d), and the species name was located in %d open-access full texts. "
                   "%d further documents (Desert Tortoise Council proceedings, IUCN species accounts, South American, Galapagos, Madagascar, Indian Ocean, Mediterranean and "
                   "Central Asian studies and theses) were saved and their tables and text checked. Only names printed in the source are linked; records taken from species "
                   "accounts or reviews are marked as such (primary study not read).") % (searched, with_hits, len(oa), docs)}},
    "scope": ("Feeding, diet, nutrition and toxicity records for catalog species from sources not used in batches 001-002. A record links a plant to a tortoise "
              "taxon as printed in the source; it is not a feeding grade and is not generalised to other tortoises."),
    "verification_levels": {
        "full_text_verified": "original paper, thesis or symposium paper read; the record is in the stated table or passage",
        "review_full_text_verified": "read in a review, species account or compilation; the primary study was not read",
        "guideline_full_text_verified": "read in a professional husbandry guideline",
        "abstract_checked": "only an abstract was read",
        "literature_lead_not_reverified": "only a title or citation was seen",
        "community_report_unverified": "keeper, forum or informant report; a reference, not verified research",
        "video_observation_unverified": "feeding as stated in a public video's title or description"},
    "ocr_corrections": {"Hibiscus rosa–sinensis": "Hibiscus rosa-sinensis"},
    "hold_names": {
        "Ceratocephalus falcatus": "gbif_synonym_is_a_homonym: GBIF resolves this name to Achillea falcata (Asteraceae), but the source means the buttercup Ceratocephala falcata (Ranunculaceae)",
        "Malcolmia lacera": "gbif_synonym_doubtful: GBIF resolves this name to Raphanus raphanistrum",
        "Areca lutescens": "misapplied_name: GBIF resolves Areca lutescens Bory to Hyophorbe indica",
        "Citrus sinensis": "gbif_synonym_doubtful: GBIF resolves sweet orange to Citrus aurantium (sour orange); most floras keep Citrus x sinensis separate",
        "Tridens pilosus": "gbif_synonym_doubtful: GBIF resolves this name to Tridentopsis mutica; it is usually treated as Erioneuron pilosum",
        "Tournefortia argentea": "gbif_synonym_doubtful: GBIF resolves this name to Heliotropium velutinum; it is usually treated as Heliotropium arboreum"},
    "common_names": [], "finding_overrides": {}, "manual_ok": [], "ocr_ok": [],
    "sources": src, "reviewed_not_feeding_evidence": [],
}
# Records whose binomial is split by OCR or a table column in the saved text; each was checked by hand (the epithet next to the
# quoted genus, or an OCR-garbled name compared with the page image).
BIN = re.compile(r"([A-Z][a-z-]+) ([a-z][a-z-]+)(?![\w-])")
for line in (B3 / "verified.jsonl").read_text(encoding="utf-8").splitlines():
    v = json.loads(line)
    if v["check"] != "name_not_in_quote" or v["plant_reported"] == "Rosmarinus":
        continue
    printed = (v.get("plant_name_expanded") or v.get("plant_reported") or "").strip()
    m = BIN.match(cfg["ocr_corrections"].get(printed, printed))
    if m:
        cfg["manual_ok"].append("|".join((v["source_id"], m.group(0), v["record_type"])))
OUT.write_text(json.dumps(cfg, ensure_ascii=False, indent=1), encoding="utf-8")
print("documents", docs, "leads", leads, "searched", searched, "with hits", with_hits, "oa", len(oa), "manual_ok", len(cfg["manual_ok"]))
