#!/usr/bin/env python3
"""QA for data/feeding_record_verification_v1.json and the catalog's feeding_pending filter.

Checks: the ledger is reproducible; feeding_pending follows its rule; A-D grades are unchanged; feeding details
appear only where an opened original states them; the catalog reads the ledger, and both languages share it.
Includes negative tests of the pending rule. Run: python scripts/qa_feeding_record_verification.py
"""
import json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import public_verdict as pv  # noqa: E402

LEDGER = ROOT / "data/feeding_record_verification_v1.json"
VERIFIED = ("original_confirmed", "prior_primary_audit_verified")
errors = []


def rule(r):
    return (r["verification_status"] in VERIFIED and r["direct_observation"] is True
            and r["plant_match"] in ("exact_species", "accepted_synonym")
            and r["plant_id"] is not None and r["existing_grade"] not in ("A", "B", "C", "D"))


before = LEDGER.read_bytes()
subprocess.run([sys.executable, str(ROOT / "scripts/build_feeding_record_verification.py")], check=True, capture_output=True)
if LEDGER.read_bytes() != before:
    LEDGER.write_bytes(before)
    errors.append("ledger is not reproducible: rerun scripts/build_feeding_record_verification.py and commit")
d = json.loads(before)

grades = {pid: pv.display(pv.representative(rows))["grade"] for pid, rows in pv.by_plant(pv.load_assessments()).items()}
pending = set()
for r in d["records"]:
    who = (r["plant_id"] or r["candidate_taxon"], r["source"])
    if r["plant_id"] and r["existing_grade"] != grades.get(r["plant_id"]):
        errors.append(f"{who}: stored grade {r['existing_grade']} != current {grades.get(r['plant_id'])}")
    if r["grade_changed"] is not False or "safety_grade" in r:
        errors.append(f"{who}: ledger must not carry or change a safety grade")
    is_pending = r["feeding_record_status"] == "feeding_pending"
    if is_pending != rule(r):
        errors.append(f"{who}: feeding_pending does not follow the rule")
    if is_pending:
        pending.add(r["plant_id"])
    if r["verification_status"] in ("not_verified", "original_inaccessible", "original_does_not_name_taxon",
                                    "recommendation_not_feeding_record") and r["feeding_record_status"] != "assessment_hold":
        errors.append(f"{who}: unverified or non-feeding source left hold")
    filled = {k: v for k, v in r["feeding_details"].items() if v is not None}
    if filled and not (r["verified_by"] or "").startswith("this ledger"):
        errors.append(f"{who}: feeding details without an opened original")
    if r["verification_status"] != "not_verified" and r["verification_status"] != "prior_primary_audit_verified" \
            and not (r["original_opened"] and r["citation"]):
        errors.append(f"{who}: checked status without the opened original and citation")
if sorted(pending) != d["site_feeding_pending"]:
    errors.append("site_feeding_pending does not match pending records")
c = d["counts"]
if c["candidates"] != len(d["records"]) or c["site_feeding_pending_plants"] != len(pending):
    errors.append("counts do not match records")

# Negative tests of the rule.
base = {"verification_status": "original_confirmed", "direct_observation": True, "plant_match": "exact_species",
        "plant_id": "x", "existing_grade": "보류"}
assert rule(base)
for change in ({"verification_status": "not_verified"}, {"verification_status": "recommendation_not_feeding_record"},
               {"direct_observation": False}, {"plant_match": "genus_or_group"}, {"plant_match": "identity_unresolved"},
               {"existing_grade": "B"}, {"plant_id": None}):
    if rule({**base, **change}):
        errors.append(f"negative test failed: {change}")

page = (ROOT / "all-plants/index.html").read_text(encoding="utf-8")
for needle in ("data/feeding_record_verification_v1.json", "ledger?.site_feeding_pending",
               "v==='feeding_pending'?r.feedingRecordPending", "'Feeding records found (under review)'",
               "'급여 기록 있음 (검증 중)'"):
    if needle not in page:
        errors.append("all-plants/index.html missing: " + needle)
if "plant_feeding_evidence_links.json" in page:
    errors.append("catalog still derives feeding_pending from unverified links")
en = (ROOT / "en/all-plants/index.html").read_text(encoding="utf-8")
if "all-plants/?lang=en" not in en:
    errors.append("English catalog no longer shares the Korean catalog page; feeding_pending parity must be rechecked")

if errors:
    print("FAIL"); [print(" -", e) for e in errors]; sys.exit(1)
print("PASS feeding record verification:", json.dumps(c, ensure_ascii=False))
