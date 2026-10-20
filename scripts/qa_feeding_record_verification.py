#!/usr/bin/env python3
"""QA for the feeding record ledger and the catalog's feeding_pending filter.

Checks: the ledger and site file are reproducible; feeding_pending follows its rule; a verified record comes only
from a full-text extract with locators; A-D grades are unchanged; feeding details are null unless stated; the
open source-data issues are recorded; the catalog reads the site file, shows summary -> details -> original link,
and both languages share it. Includes negative tests. Run: python scripts/qa_feeding_record_verification.py
"""
import json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import public_verdict as pv  # noqa: E402

LEDGER = ROOT / "data/feeding_record_verification_v1.json"
SITE = ROOT / "data/feeding_pending_site_v1.json"
EXTRACTS = ROOT / "data/feeding_record_fulltext_extracts_v1.json"
ISSUES = ROOT / "data/feeding_record_source_qa_issues_v1.json"
GRADED = ("A", "B", "C", "D")
errors = []


def link_rule(rec, link):
    return bool(rec["verification_status"] == "full_text_confirmed" and rec["feeding_fact_confirmed"] is True
                and rec["identity_resolved"] is True and rec["gbif_key"] is not None and link["grade"] not in GRADED)


before = {p: p.read_bytes() for p in (LEDGER, SITE)}
subprocess.run([sys.executable, str(ROOT / "scripts/build_feeding_record_verification.py")], check=True, capture_output=True)
for p, b in before.items():
    if p.read_bytes() != b:
        p.write_bytes(b)
        errors.append(f"{p.name} is not reproducible: rerun scripts/build_feeding_record_verification.py and commit")
d, site = json.loads(before[LEDGER]), json.loads(before[SITE])
ext = json.loads(EXTRACTS.read_text(encoding="utf-8"))

grades = {pid: pv.display(pv.representative(rows))["grade"] for pid, rows in pv.by_plant(pv.load_assessments()).items()}

# Full-text extracts: each source read in full, each record with a locator; names with homonyms not resolved.
for s in ext["sources"]:
    if not (s.get("full_text") and s.get("method_locator") and s.get("url") and s.get("citation")):
        errors.append(f"extract source {s['source_key']}: missing full-text access, locator, url or citation")
    if "abstract" in s["full_text"].lower():
        errors.append(f"extract source {s['source_key']}: an abstract is not a full text")
for r in ext["records"]:
    if r["gbif_key"] is None and r["gbif_match"].startswith("EXACT"):
        errors.append(f"extract {r['plant_taxon_reported']}: exact match without a key")
    if r["gbif_key"] is not None and not r["gbif_match"].startswith("EXACT"):
        errors.append(f"extract {r['plant_taxon_reported']}: linked through a non-exact name match")
    if re.search(r"\bspp?\.", r["plant_taxon_reported"]):
        errors.append(f"extract {r['plant_taxon_reported']}: genus-level name used as a record")
    for f in ("plant_part", "observed"):
        if r[f] is not None and not (r[f].get("ko") and r[f].get("en") and r[f].get("locator")):
            errors.append(f"extract {r['plant_taxon_reported']}: {f} needs ko, en and a locator")

pending = set()
for rec in d["fulltext_records"]:
    if rec["feeding_details"] != {"mixed_with": None, "feeding_frequency": None, "feeding_amount": None,
                                  "fresh_or_dried": None, "preparation": None}:
        errors.append(f"{rec['plant_taxon_reported']}: feeding practice details are not stated by any read original")
    for link in rec["links"]:
        if link["kind"] == "reviewed_plant" and link["grade"] != grades.get(link["id"]):
            errors.append(f"{link['id']}: stored grade {link['grade']} != current {grades.get(link['id'])}")
        if link["feeding_pending"] != link_rule(rec, link):
            errors.append(f"{rec['plant_taxon_reported']} -> {link['id']}: feeding_pending does not follow the rule")
        if link["feeding_pending"]:
            pending.add(link["id"])
if sorted(pending) != d["site_feeding_pending"] or d["site_feeding_pending"] != site["site_feeding_pending"]:
    errors.append("site_feeding_pending does not match the pending links")
if set(site["records"]) != pending:
    errors.append("site records do not cover exactly the pending ids")

for r in d["records"]:
    who = (r["plant_id"] or r["candidate_taxon"], r["source"])
    if r["plant_id"] and r["existing_grade"] != grades.get(r["plant_id"]):
        errors.append(f"{who}: stored grade {r['existing_grade']} != current {grades.get(r['plant_id'])}")
    if r["grade_changed"] is not False or "safety_grade" in r:
        errors.append(f"{who}: ledger must not carry or change a safety grade")
    if r["verification_status"] == "full_text_confirmed" and not r["original_locator"]:
        errors.append(f"{who}: confirmed without a locator")
c = d["counts"]
if c["candidates"] != len(d["records"]) or c["site_feeding_pending"] != len(pending):
    errors.append("counts do not match records")

# Negative tests of the pending rule.
base_rec = {"verification_status": "full_text_confirmed", "feeding_fact_confirmed": True, "identity_resolved": True, "gbif_key": 1}
base_link = {"grade": None}
assert link_rule(base_rec, base_link)
for rc, lc in (({"verification_status": "abstract_only_not_confirmed"}, {}), ({"feeding_fact_confirmed": False}, {}),
               ({"identity_resolved": False, "gbif_key": None}, {}), ({}, {"grade": "B"}), ({}, {"grade": "D"})):
    if link_rule({**base_rec, **rc}, {**base_link, **lc}):
        errors.append(f"negative test failed: {rc} {lc}")

# Source-data issues found while checking originals stay recorded until fixed by their owner.
issues = {i["id"]: i for i in json.loads(ISSUES.read_text(encoding="utf-8"))["issues"]}
for iid, needle in (("QA-FR-001", "El Mouden"), ("QA-FR-002", "leaves")):
    if iid not in issues or needle not in json.dumps(issues[iid]):
        errors.append(f"source-data issue {iid} is not recorded")
for i in issues.values():
    for loc in i["locations"]:
        if not (ROOT / loc["file"]).exists():
            errors.append(f"{i['id']}: location {loc['file']} does not exist")

page = (ROOT / "all-plants/index.html").read_text(encoding="utf-8")
for needle in ("data/feeding_pending_site_v1.json", "ledger?.site_feeding_pending",
               "v==='feeding_pending'?r.feedingRecordPending", "feedingRecordPending:feedingIds.has(t.taxon_id)",
               "'Feeding records found (under review)'", "'급여 기록 있음 (검증 중)'", "function feedHTML(r)",
               "'원문 보기 ↗'", "'Open the original ↗'"):
    if needle not in page:
        errors.append("all-plants/index.html missing: " + needle)
f = page[page.index("function feedHTML(r)"):page.index("function emptyHTML(){")]
ret, body = f[f.index("return '<div class=\"feedrec\""):], f[f.index("const body="):]
if not (ret.index("feedsum") < ret.index("<details>") < ret.index("+body+") and body.index("<dl>") < body.index("feedsrc")):
    errors.append("feeding record block is not ordered summary -> details -> original link")
if "plant_feeding_evidence_links.json" in page:
    errors.append("catalog still derives feeding_pending from unverified links")
en = (ROOT / "en/all-plants/index.html").read_text(encoding="utf-8")
if "all-plants/?lang=en" not in en:
    errors.append("English catalog no longer shares the Korean catalog page; feeding_pending parity must be rechecked")

if errors:
    print("FAIL"); [print(" -", e) for e in errors]; sys.exit(1)
print("PASS feeding record verification:", json.dumps(c, ensure_ascii=False))
