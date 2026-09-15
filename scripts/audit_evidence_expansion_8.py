from pathlib import Path
import json, re

R = Path(__file__).resolve().parents[1]
DATA = R / "data"

def addendum_order(path):
    m = re.search(r"_(\d+)\.json$", path.name)
    return int(m.group(1)) if m else 0

assessment_files = [DATA / "assessments.json"] + sorted(
    DATA.glob("assessments_korea_addendum*.json"), key=addendum_order
)
assessments = []
for path in assessment_files:
    assessments.extend(json.loads(path.read_text(encoding="utf-8")))

evidence = json.loads((DATA / "evidence.json").read_text(encoding="utf-8"))
for path in sorted(DATA.glob("evidence_korea_addendum*.json"), key=addendum_order):
    evidence.extend(json.loads(path.read_text(encoding="utf-8")))
plants = json.loads((DATA / "plants.json").read_text(encoding="utf-8"))

E = {x["id"]: x for x in evidence}
P = {x["id"]: x for x in plants}

def records(plant_id, species_group):
    return [x for x in assessments if x.get("plant_id") == plant_id and x.get("species_group") == species_group]

def latest(plant_id, species_group):
    rows = records(plant_id, species_group)
    if not rows:
        raise KeyError((plant_id, species_group))
    return rows[-1]

def lineage_text(plant_id, species_group, field):
    vals = []
    for row in records(plant_id, species_group):
        value = row.get(field, [])
        vals.extend(value if isinstance(value, list) else [value])
    return " ".join(str(v) for v in vals)

def lineage_ids(plant_id, species_group):
    ids = set()
    for row in records(plant_id, species_group):
        ids.update(row.get("evidence_ids", []))
    return ids

alfalfa = latest("alfalfa", "Mediterranean_Testudo")
dolnamul = latest("dolnamul", "Tortoise_general")
alfalfa_limits = lineage_text("alfalfa", "Mediterranean_Testudo", "limits")
dolnamul_limits = lineage_text("dolnamul", "Tortoise_general", "limits")

checks = {
    "alfalfa_master_identity": P["alfalfa"]["scientific"] == "Medicago sativa",
    "alfalfa_limited_not_staple": alfalfa["verdict"] == "limited_mixed_diet",
    "alfalfa_genus_limit_visible": "Medicago sp." in alfalfa_limits,
    "alfalfa_no_exact_ibera_overclaim": "자동 승격하지 않음" in alfalfa_limits,
    "alfalfa_direct_evidence_two_regions": {"iftime_ibera_dobrogea_2012", "mitrevichin_ibera_bulgaria_2023"}.issubset(lineage_ids("alfalfa", "Mediterranean_Testudo")),
    "dolnamul_master_identity": P["dolnamul"]["scientific"] == "Sedum sarmentosum",
    "dolnamul_not_mediterranean_direct": not records("dolnamul", "Mediterranean_Testudo"),
    "dolnamul_limited_general": dolnamul["verdict"] == "limited_supplement",
    "dolnamul_species_gap_visible": "Sedum rubens" in dolnamul_limits and "S. album" in dolnamul_limits,
    "dolnamul_sedum_acre_warning": "Sedum acre" in dolnamul_limits,
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
