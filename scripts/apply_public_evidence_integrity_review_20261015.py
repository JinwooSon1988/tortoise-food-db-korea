#!/usr/bin/env python3
"""Re-runnable application of the 2026-10-15 public evidence integrity review.

The decision record is data/public_evidence_integrity_review_20261015.json (each change with its reason, the
verification level actually reached and the value before). This script writes exactly those changes, then gives
every public evidence record its `source_id` (scripts/evidence_sources.py), and updates the Tortoise Table link
audit for the records whose listing-page link was replaced. No record is deleted; verdicts are not changed.

A field is written only while it still holds the review's "before" value. A field edited after the review (a
value that is neither "before" nor "after") is left as it is and listed as skipped, so a re-run never undoes a
later correction. A link audit entry is rewritten only while it still holds the listing-page link. CI does not
re-run this script; the guarantees it set up are checked by scripts/qa_public_evidence_integrity_v1.py.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from evidence_sources import computed_source_id

REVIEW = json.loads((ROOT / "data/public_evidence_integrity_review_20261015.json").read_text(encoding="utf-8"))
A_PATH = ROOT / "data/public_assessments.json"
E_PATH = ROOT / "data/public_evidence_records.json"
L_PATH = ROOT / "data/tortoise_table_link_audit_20261010.json"


def with_source_fields(r):
    """Key order: id, source_id, same_finding_as (when set), then the record's own fields."""
    out = {"id": r["id"], "source_id": computed_source_id(r)}
    if r.get("same_finding_as"):
        out["same_finding_as"] = r["same_finding_as"]
    out.update({k: v for k, v in r.items() if k not in out and k != "same_finding_as"})
    return out


def apply_fields(target, upd, label, skipped):
    """Write each reviewed field that still holds its "before" value; leave later edits alone."""
    for k, new in upd["after"].items():
        cur = target.get(k)
        if cur == new:
            continue
        if cur == upd["before"].get(k):
            target[k] = new
        else:
            skipped.append(f"{label}.{k}")


def main():
    assess = json.loads(A_PATH.read_text(encoding="utf-8"))
    evid = json.loads(E_PATH.read_text(encoding="utf-8"))
    links = json.loads(L_PATH.read_text(encoding="utf-8"))
    by_id = {r["id"]: r for r in evid["records"]}
    skipped = []
    for upd in REVIEW["evidence_updates"]:
        apply_fields(by_id[upd["id"]], upd, upd["id"], skipped)
    for item in REVIEW["assessment_updates"]:
        rows = [a for a in assess if a["plant_id"] == item["plant_id"] and a["species_group"] == item["species_group"]]
        assert len(rows) == 1, item["plant_id"]
        apply_fields(rows[0], item, f"{item['plant_id']}|{item['species_group']}", skipped)
    evid["records"] = [with_source_fields(r) for r in evid["records"]]

    audit = {r["record_id"]: r for r in links["records"]}
    for upd in REVIEW["evidence_updates"]:
        if upd["kind"] != "listing_page_replaced":
            continue
        v = upd["verification"]
        a = audit[upd["id"]]
        if a["url"] == v["url"]:
            continue
        if a["url"] != upd["before"]["url"]:
            skipped.append(f"link audit {upd['id']}")
            continue
        a["previous_url"] = a["url"]
        a.update({"checked_at": v["checked_at"], "url": v["url"], "name": v["page_name"], "latin": v["page_latin"], "classification": v["page_classification"]})
        a.pop("note", None)
        a["correction"] = "2026-10-15: listing/search page replaced by the plant's own entry (link taken from the site's A-Z list); see data/public_evidence_integrity_review_20261015.json"
    links["summary"]["listing_pages_replaced_20261015"] = sum(1 for u in REVIEW["evidence_updates"] if u["kind"] == "listing_page_replaced")

    A_PATH.write_text(json.dumps(assess, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    E_PATH.write_text(json.dumps(evid, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    L_PATH.write_text(json.dumps(links, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("applied:", len(REVIEW["evidence_updates"]), "evidence updates,", len(REVIEW["assessment_updates"]), "assessment updates;",
          len({r["source_id"] for r in evid["records"]}), "sources for", len(evid["records"]), "records")
    if skipped:
        print("left unchanged (edited after the review):", ", ".join(skipped))


if __name__ == "__main__":
    main()
