"""Canonical public verdict selection for generated pages and QA.

Mirrors verdict-core.js (used by the home search). scripts/qa_verdict_consistency.py
runs both implementations against data/public_assessments.json and the generated
detail pages, so the home and detail grade can never drift apart.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

GRADES = {
    "supported_mixed_diet": {"grade": "A", "label": "적극 권장", "tone": "green", "meaning": "여러 적합한 식물을 섞는 일상 혼합식의 주요 구성으로 활용하기 좋다."},
    "limited_mixed_diet": {"grade": "B", "label": "제한적 혼합 급여", "tone": "teal", "meaning": "혼합식에 넣을 수 있지만 사용 범위에 제한이 있다. 한 종류에 식단을 편중하지 않는다."},
    "limited_supplement": {"grade": "C", "label": "가끔 보조 급여", "tone": "yellow", "meaning": "주식이 아니라 가끔 곁들이는 보조 먹이로만 본다."},
    "limited": {"grade": "C", "label": "제한 급여", "tone": "yellow", "meaning": "주식이나 반복적인 대량 급여에는 쓰지 않고, 다양한 식단에서 제한적으로만 사용한다."},
    "supplement_general_evidence": {"grade": "C", "label": "가끔 보조 급여", "tone": "yellow", "meaning": "주식이 아니라 가끔 곁들이는 보조 먹이로만 본다."},
    "general_reptile_supplement": {"grade": "C", "label": "가끔 보조 급여", "tone": "yellow", "meaning": "주식이 아니라 가끔 곁들이는 보조 먹이로만 본다."},
    "do_not_feed": {"grade": "D", "label": "계획 급여에서 제외", "tone": "danger", "meaning": "일상 식단에 계획적으로 넣지 않는다. 우발적 소량 섭취의 독성과는 별개의 판정이다."},
}
HOLD = {"grade": "보류", "label": "판정 보류", "tone": "hold", "meaning": "근거가 부족하거나 엇갈려 등급을 정하지 않았다. 보류는 안전하다는 뜻이 아니다."}
NO_DEFAULT = {"grade": "보류", "label": "판정 보류", "tone": "hold", "meaning": "공통 급여 판정이 아직 없다. 판정이 없다는 것은 안전하다는 뜻이 아니다."}


def load_assessments():
    data = json.loads((ROOT / "data/public_assessments.json").read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = data.get("assessments", data.get("records", []))
    return data


def is_species_only(a):
    return a.get("assessment_scope") == "exact_species" and bool(a.get("animal_taxon")) and a.get("animal_taxon") != "Testudo"


def representative(rows):
    rows = rows or []
    for test in (
        lambda x: x.get("animal_taxon") == "Testudo",
        lambda x: x.get("species_group") == "Mediterranean_Testudo",
        lambda x: x.get("assessment_scope") == "tortoise_general",
        lambda x: x.get("species_group") == "Tortoise_general",
        lambda x: not is_species_only(x),
    ):
        for x in rows:
            if test(x):
                return x
    return None


def display(a):
    if not a:
        return NO_DEFAULT
    return GRADES.get(a.get("verdict"), HOLD)


def species_notes(rows, primary):
    return [x for x in rows or [] if x is not primary and is_species_only(x)]


def scope_label(a):
    if not a:
        return "공통 급여 판정 없음"
    if a.get("animal_taxon") == "Testudo" or a.get("species_group") == "Mediterranean_Testudo":
        return "지중해 Testudo 근거"
    if a.get("assessment_scope") == "tortoise_general" or a.get("species_group") == "Tortoise_general":
        return "육지거북 일반 근거"
    if a.get("species_group") == "Herbivorous_reptile_general" or a.get("assessment_scope") == "herbivorous_reptile_general":
        return "초식 파충류 일반 근거"
    return "간접 근거"


def by_plant(assessments):
    out = {}
    for a in assessments:
        out.setdefault(a["plant_id"], []).append(a)
    return out


def public_plants(plants, assessments):
    """Same rule as the home catalog: non-candidate plants with at least one public assessment."""
    assessed = {a["plant_id"] for a in assessments}
    return [p for p in plants if p.get("identity_status") != "candidate_name" and p.get("id") in assessed]
