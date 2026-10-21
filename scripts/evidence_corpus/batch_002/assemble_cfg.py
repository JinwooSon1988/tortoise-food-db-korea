"""Assemble the batch-002 config from the per-area source settings and the agents' search logs. Writes b2_config.json."""
import json, collections
from pathlib import Path

HERE = Path(__file__).parent
B2 = HERE / "b2"
src = {}
for f in ["b2_config_africa.json", "b2_config_more.json", "b2_config_testudo.json", "b2_config_forums.json"]:
    if (HERE / f).exists():
        src.update(json.loads((HERE / f).read_text(encoding="utf-8")))
read = collections.Counter(); leads = 0; classes = collections.Counter()
for d in sorted(p for p in B2.iterdir() if p.is_dir() and (p / "sources.jsonl").exists()):
    for line in (d / "sources.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            s = json.loads(line); read[d.name] += 1; classes[s.get("source_class") or "other"] += 1
    if (d / "leads.jsonl").exists():
        leads += sum(1 for line in (d / "leads.jsonl").read_text(encoding="utf-8").splitlines() if line.strip())
n = sum(read.values())
cfg = {
 "batch": "batch-002", "built": "2026-10-21",
 "corpus": {
  "id": "corpus-2026-10-21-b2", "searched": "2026-10-21",
  "searches": [
   {"area": "African tortoises (sulcata, leopard, Chersina, Kinixys, pancake, Egyptian)", "languages": ["en", "fr", "de"],
    "services": "web search; South African, Tanzanian and Dutch university repositories; IUCN TFTSG accounts; chelonian.org"},
   {"area": "Testudo, priority Russian tortoise", "languages": ["ru", "zh", "de", "fr", "it", "es", "el", "en"],
    "services": "web search; cyberleninka; open journal archives; repositories"},
   {"area": "Radiated, star, Indotestudo, Manouria, Pyxis", "languages": ["en", "fr", "ja", "zh"],
    "services": "web search; IUCN TFTSG and Red List accounts; BHL via archive.org; Zoos' Print; EAZA"},
   {"area": "Zoo, government and veterinary guidelines; nutrition; toxicity; keeper sites", "languages": ["en", "de", "fr", "ja", "ko"],
    "services": "web search; EAZA; Merck Veterinary Manual; PubMed E-utilities; keeper society pages"},
   {"area": "Theses and grey literature in the Americas; Japanese, Korean, Chinese sources", "languages": ["en", "pt", "es", "ja", "ko", "zh"],
    "services": "web search; J-STAGE and DOAJ APIs; Brazilian, Argentine, Ecuadorian and US repositories"},
   {"area": "YouTube, Reddit, Instagram, Facebook, English-language forums", "languages": ["en", "ko", "ja", "zh"],
    "services": "web search; YouTube public watch-page metadata and oEmbed only (no video downloaded or watched); forum threads where robots.txt allows"},
   {"area": "Non-English keeper forums and zoo keeper diaries", "languages": ["de", "fr", "it", "es", "nl", "ru", "ja", "ko", "zh"],
    "services": "web search; public pages where robots.txt and site terms allow"}],
  "documents_read": n, "documents_by_class": dict(classes), "leads_not_accessed": leads,
  "not_accessible": "Reddit (robots.txt disallows all; the API needs OAuth), Instagram and Facebook (login), tortoiseforum.org (bot challenge), "
                    "The Tortoise Table and testudo-farm.de (terms forbid reuse), J-STAGE PDFs and a Chinese wildlife journal (robots.txt), "
                    "paywalled journals and pages behind bot challenges. Nothing was bypassed.",
  "screening": "Seven research passes saved every document used as text; each record carries a verbatim quote that a script re-found in the saved "
               "text, together with the plant name. Records whose quote or name could not be re-found, names printed only as common names or to genus, "
               "and keeper, forum or video posts without a scientific name are held, not linked.",
  "summary": {
   "ko": "동물원·정부·수의학 사육지침, 학위논문, 종 설명서, 영양·독성 자료, 사육자 커뮤니티와 공개 영상 정보를 다국어(영·불·독·서·포·러·중·일·한 등)로 조사해 문서 %d건을 저장·확인했습니다. 학명이 원문에 인쇄된 기록만 연결했고, 커뮤니티·영상 자료는 검증 연구와 구분해 참고용으로 표시합니다. 로그인·약관·robots 제한이 있는 Reddit·Instagram·Facebook 등은 수집하지 않았습니다." % n,
   "en": "Zoo, government and veterinary husbandry guidelines, theses, species accounts, nutrition and toxicity sources, keeper communities and public video metadata were searched in several languages (English, French, German, Spanish, Portuguese, Russian, Chinese, Japanese, Korean and more); %d documents were saved and checked. Only records whose source prints a scientific name are linked, and community and video reports are shown apart from verified research, for reference only. Reddit, Instagram, Facebook and other sites behind logins, terms or robots.txt limits were not collected." % n}},
 "scope": "Feeding, husbandry, nutrition and toxicity records for catalog species from sources outside the open-access paper search of batch 001. "
          "A record links a plant to a tortoise taxon as printed in the source; it is not a feeding grade and is not generalised to other tortoises.",
 "verification_levels": {
  "full_text_verified": "academic original (paper or thesis) read; the record is in the stated table or passage",
  "review_full_text_verified": "read in a review, species account or fact sheet; the primary study was not read",
  "guideline_full_text_verified": "read in a professional husbandry guideline (zoo association, government or veterinary source)",
  "abstract_checked": "only the abstract was read",
  "literature_lead_not_reverified": "only a title or citation was seen",
  "community_report_unverified": "keeper, forum or informant report; a reference, not verified research",
  "video_observation_unverified": "feeding as stated in a public video's title or description; the video itself was not verified"},
 "ocr_corrections": {"Cissus quadrangularts": "Cissus quadrangularis"},
 "hold_names": {
  "Ceratocephalus falcatus": "gbif_synonym_is_a_homonym: GBIF resolves this name to Achillea falcata (Asteraceae), but the source means the buttercup Ceratocephala falcata (Ranunculaceae)",
  "Malcolmia lacera": "gbif_synonym_doubtful: GBIF resolves this name to Raphanus raphanistrum; the Doñana table most likely means Malcolmia (Maresia) lacera",
  "Areca lutescens": "misapplied_name: GBIF resolves Areca lutescens Bory to Hyophorbe indica, but in Brazilian usage the name means the areca palm Dypsis lutescens"},
 "finding_overrides": {"richard1994_cuadherpetol|Prosopis alpataco|captive_feeding_record": {
   "ko": "사육 성체 5마리에게 이 꼬투리만 3일간 주었을 때 이상이 관찰되지 않았다고 기록 (원문은 일부 Prosopis 종에 강한 독성 알칼로이드가 보고되었다고 함께 적음; 짧은 시험이며 안전성 입증이 아님)",
   "en": "Five captive adults fed only these pods for three days showed no disorder (the source also notes that strongly toxic alkaloids have been reported in some Prosopis species; a short test, not proof of safety)"}},
 "manual_ok": ["richard1994_cuadherpetol|Prosopis alpataco|captive_feeding_record"],
 "ocr_ok": ["Cynodon dactylon", "Opuntia ficus-indica", "Abutilon sonneratianum", "Bulbine abyssinica"],
 "sources": src,
 "reviewed_not_feeding_evidence": [],
}
(HERE / "b2_config.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=1), encoding="utf-8")
print("documents", n, dict(read), "leads", leads)
