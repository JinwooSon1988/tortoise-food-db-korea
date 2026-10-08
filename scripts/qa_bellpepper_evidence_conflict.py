#!/usr/bin/env python3
"""Ensure conflicting bell pepper husbandry guidance is not hidden by USDA nutrition."""
import json
from pathlib import Path
root = Path(__file__).resolve().parents[1]
review = json.loads((root / "data/bellpepper_feeding_evidence_reassessment_20261008.json").read_text(encoding="utf-8"))
nutrients = json.loads((root / "data/usda_bellpepper_original_csv_verified_20261008.json").read_text(encoding="utf-8"))
page = (root / "plant/bellpepper/index.html").read_text(encoding="utf-8")
assert review["plant_id"] == "bellpepper"
assert review["review_status"] == "evidence_conflict__requires_feeding_grade_review"
assert review["feeding_grade_changed"] is False
assert any("thetortoisetable.org.uk" in item["url"] for item in review["source_positions"])
assert len(nutrients["records"]) == 7
assert 'data-grade="C"' in page, "Current grade changed without explicit review"
assert "영양성분 수치가 급여 허용을 뜻하지는 않습니다." in page
assert "급여하지 않음" in page
assert "USDA" in page
print("OK: evidence conflict documented, USDA nutrition separate, current grade unchanged")
