#!/usr/bin/env python3
"""Regression tests for scripts/audit_evidence_conflicts.py.

Each case copies the canonical data to a temporary folder, reintroduces one known error class and checks that
the audit reports it at error level. The untouched copy must report no unaccepted error.

Run: python scripts/test_audit_evidence_conflicts.py
"""
import json, shutil, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import audit_evidence_conflicts as A  # noqa: E402

FILES = ["data/plants.json", "data/public_assessments.json", "data/public_evidence_records.json",
         "data/plant_feeding_evidence_links.json", "data/reviewed_plant_reverse_evidence_index.json",
         "data/feeding_record_verification_v1.json", "data/feeding_record_fulltext_extracts_v1.json",
         "data/verified_plant_images_v56.json", "data/i18n/en/strings_en.json", "data/source_access_check_20261019.json",
         "data/feeding_p1_blocked_claim_manifest_20261018.json"]
RUSCUS = "wild_ruscus_aculeatus_thh_italy_2011"


def copy(tmp):
    for rel in FILES:
        if (ROOT / rel).exists():
            (tmp / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(ROOT / rel, tmp / rel)


def edit(tmp, rel, fn):
    p = tmp / rel
    d = json.loads(p.read_text(encoding="utf-8"))
    fn(d)
    p.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")


def pub_rec(d, rid):
    return next(r for r in d["records"] if r["id"] == rid)


def ruscus_assessment(d):
    return next(a for a in d if a["plant_id"] == "ruscus_aculeatus")


def first_direct(d):
    return next(r for r in d["records"] if r["directness"] == "direct")


def ledger_ruscus(d):
    return next(r for r in d["records"] if r.get("plant_id") == "ruscus_aculeatus")


CASES = [
    ("R13_ruscus_parts_not_distinguished", "data/public_evidence_records.json",
     lambda d: pub_rec(d, RUSCUS).update(plant_part_state="fruits and seeds (Table 1); flowers and unripe fruit (abstract); leaves not reported")),
    ("R2_part_drift_links_vs_public", "data/plant_feeding_evidence_links.json",
     lambda d: next(e for r in d["records"] for e in r["evidence"] if e["evidence_id"] == RUSCUS).update(plant_part="leaves")),
    ("R13_ruscus_parts_not_distinguished", "data/public_assessments.json",
     lambda d: ruscus_assessment(d).update(why=ruscus_assessment(d)["why"].replace("Discussion(p. 245)", "본문"))),
    ("R13_ruscus_grade_changed", "data/public_assessments.json", lambda d: ruscus_assessment(d).update(confidence="C")),
    ("R13_ruscus_ledger_overstated", "data/feeding_record_verification_v1.json",
     lambda d: ledger_ruscus(d).update(verification_status="full_text_confirmed")),
    ("R9_public_cites_original_ledger_unverified", "data/feeding_record_verification_v1.json",
     lambda d: ledger_ruscus(d).update(verification_status="abstract_only_not_confirmed")),
    ("R5_assessment_part_not_in_evidence", "data/public_assessments.json",
     lambda d: ruscus_assessment(d).update(why=ruscus_assessment(d)["why"] + " 야생 헤르만육지거북이 뿌리도 섭식했다.")),
    ("R3_direct_without_tortoise_taxon", "data/public_evidence_records.json",
     lambda d: first_direct(d).update(animal_taxon="Plant composition")),
    ("R8_doi_field_url_mismatch", "data/public_evidence_records.json",
     lambda d: pub_rec(d, RUSCUS).update(url="https://doi.org/10.1000/unrelated.1")),
    ("R14_duplicate_source_records", "data/public_evidence_records.json",
     lambda d: d["records"].append({**pub_rec(d, RUSCUS), "id": RUSCUS + "_copy"})),
    ("R1_unknown_plant_id", "data/public_evidence_records.json",
     lambda d: pub_rec(d, RUSCUS).update(plant_ids=["ruscus_aculeatus", "no_such_plant"])),
    ("R15_held_source_shown_as_direct_without_disclosure", "data/public_evidence_records.json",
     lambda d: pub_rec(d, "wild_medicago_polymorpha_tgg_morocco").update(
         supports=pub_rec(d, "wild_medicago_polymorpha_tgg_morocco")["supports"].split(" 다만 이 출처의")[0])),
    ("R11_image_master_name_drift", "data/verified_plant_images_v56.json",
     lambda d: d["images"][0].update(master_scientific="Wrongus name")),
]


def errors(tmp):
    findings = A.audit(tmp)
    return {(f["rule"], f["ref"]) for f in findings if f["severity"] == "error" and f"{f['rule']}|{f['ref']}" not in A.ACCEPTED}


def main():
    failed = []
    with tempfile.TemporaryDirectory() as t:
        base = Path(t) / "base"
        copy(base)
        if errors(base):
            failed.append(f"clean copy reports errors: {sorted(errors(base))[:5]}")
        for i, (rule, rel, fn) in enumerate(CASES):
            tmp = Path(t) / f"case{i}"
            copy(tmp)
            edit(tmp, rel, fn)
            got = {r for r, _ in errors(tmp)}
            if rule not in got:
                failed.append(f"case {i}: expected {rule}, got {sorted(got) or 'no error'}")
    for f in failed:
        print("FAIL", f)
    if failed:
        sys.exit(f"{len(failed)} audit regression test(s) failed")
    print(f"PASS: clean data has no unaccepted errors; {len(CASES)} injected error classes detected")


if __name__ == "__main__":
    main()
