from pathlib import Path
import json

R = Path(__file__).resolve().parents[1]
assessments = json.loads((R / "data/assessments.json").read_text(encoding="utf-8"))
evidence = json.loads((R / "data/evidence.json").read_text(encoding="utf-8"))
plants = json.loads((R / "data/plants.json").read_text(encoding="utf-8"))

A = {(x["plant_id"], x["species_group"]): x for x in assessments}
E = {x["id"]: x for x in evidence}
P = {x["id"]: x for x in plants}

alfalfa = A[("alfalfa", "Mediterranean_Testudo")]
dolnamul = A[("dolnamul", "Tortoise_general")]

checks = {
    "alfalfa_master_identity": P["alfalfa"]["scientific"] == "Medicago sativa",
    "alfalfa_limited_not_staple": alfalfa["verdict"] == "limited_mixed_diet",
    "alfalfa_genus_limit_visible": "Medicago sp." in " ".join(alfalfa.get("limits", [])),
    "alfalfa_no_exact_ibera_overclaim": "자동 승격하지 않음" in " ".join(alfalfa.get("limits", [])),
    "alfalfa_direct_evidence_two_regions": {"iftime_ibera_dobrogea_2012", "mitrevichin_ibera_bulgaria_2023"}.issubset(set(alfalfa["evidence_ids"])),
    "dolnamul_master_identity": P["dolnamul"]["scientific"] == "Sedum sarmentosum",
    "dolnamul_not_mediterranean_direct": ("dolnamul", "Mediterranean_Testudo") not in A,
    "dolnamul_limited_general": dolnamul["verdict"] == "limited_supplement",
    "dolnamul_species_gap_visible": "Sedum rubens" in " ".join(dolnamul.get("limits", [])) and "S. album" in " ".join(dolnamul.get("limits", [])),
    "dolnamul_sedum_acre_warning": "Sedum acre" in " ".join(dolnamul.get("limits", [])),
    "tortoise_table_sedum_present": "tortoise_table_sedum" in E,
    "korean_dolnamul_identity_present": E["korean_dolnamul_identity"]["taxon"] == "Sedum sarmentosum",
    "testudo_doi_verified": E["testudo2018"].get("doi") == "10.1080/10888705.2018.1453814",
    "testudo_pmid_verified": E["testudo2018"].get("pmid") == "29609473",
    "alfalfa_page_yellow": "🟡 제한적 혼합급여 근거" in (R / "plant/alfalfa/index.html").read_text(encoding="utf-8"),
    "dolnamul_page_yellow": "🟡 제한적 보조식 근거" in (R / "plant/dolnamul/index.html").read_text(encoding="utf-8"),
}

for k, v in checks.items():
    print(("PASS" if v else "FAIL"), k)

failed = [k for k, v in checks.items() if not v]
if failed:
    raise SystemExit("Evidence expansion 8 audit failed: " + ", ".join(failed))
print("Evidence expansion 8 audit PASS")
