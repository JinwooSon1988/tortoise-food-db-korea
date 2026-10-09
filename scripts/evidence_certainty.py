"""Reader-facing wording for an assessment's `confidence` code (evidence certainty).

The code (A, B+, B, B-, C+, C, C-, D…) is stored in data/public_assessments.json. It uses the same letters as the
feeding grade (A–D), so pages show it in words under the label "근거 확실성" and never as a bare letter next to the
grade. The same mapping is inlined in index.html and all-plants/index.html (CERTAINTY_KO); QA:
scripts/qa_evidence_certainty_labels_v1.py keeps the copies identical.
"""
CERTAINTY_LABEL = "근거 확실성"
CERTAINTY_KO = {
    "A": "높음", "B+": "다소 높음", "B": "중간", "B-": "중간 이하",
    "C+": "다소 낮음", "C": "낮음", "C-": "매우 낮음",
    "D+": "매우 낮음", "D": "매우 낮음", "D-": "매우 낮음",
}
UNKNOWN = "미확정"


def certainty_ko(code):
    return CERTAINTY_KO.get(str(code or "").strip(), UNKNOWN)
