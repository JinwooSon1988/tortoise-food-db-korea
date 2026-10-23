#!/usr/bin/env python3
"""Validate Batch 002 provenance, exact-name matching and site wiring before merge."""
import collections
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
BATCH = ROOT / "data/catalog-evidence/batch-002-20261021.json"
PAGE = ROOT / "taxon/index.html"
ALLOWED = {
    "full_text_verified", "review_full_text_verified",
    "guideline_full_text_verified", "abstract_checked",
    "literature_lead_not_reverified", "community_report_unverified",
    "video_observation_unverified",
}
def main():
    data = json.loads(BATCH.read_text(encoding="utf-8"))
    sources = {s["source_key"]: s for s in data["sources"]}
    assert len(sources) == len(data["sources"]), "Duplicate source keys"
    records = data["records"]
    assert records, "No evidence records"
    errors = []
    by_verification = collections.Counter()
    names = set()
    for i, record in enumerate(records):
        name = str(record.get("reported_name") or "").strip()
        source = sources.get(record.get("source_key"))
        if not source:
            errors.append(f"{i}: source missing")
        elif not re.match(r"^https?://", str(source.get("url") or "")):
            errors.append(f"{i}: missing valid web source URL")
        if not re.match(r"^[A-Z][a-z-]+ [a-z][a-z-]+$", name):
            errors.append(f"{i}: not an exact binomial: {name!r}")
        if not str(record.get("tortoise") or "").strip():
            errors.append(f"{i}: missing tortoise taxon")
        if not str(record.get("locator") or "").strip():
            errors.append(f"{i}: missing source locator")
        if record.get("verification") not in ALLOWED:
            errors.append(f"{i}: unknown verification")
        if any(k in record for k in ("grade", "feeding_grade", "safe_to_feed")):
            errors.append(f"{i}: unsupported safety grade")
        by_verification[record.get("verification")] += 1
        names.add(name.casefold())
    index_path = ROOT / "data/catalog-evidence/batch-002-site-index.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    grouped = collections.defaultdict(list)
    for record in records:
        grouped[record["reported_name"].strip().casefold()].append(record)
    if index.get("by_scientific_name") != dict(grouped):
        errors.append("Site index does not match source records exactly")
    if index.get("sources") != data["sources"]:
        errors.append("Site index source metadata differs from corpus")
    if index.get("stats", {}).get("records") != len(records):
        errors.append("Site index record count differs from corpus")
    if index.get("stats", {}).get("distinct_reported_names") != len(grouped):
        errors.append("Site index unique-name count differs from corpus")
    # Publication contract: only evidence-linked catalog taxa may appear in the
    # public catalog or resolve to a public detail page. Keep the reviewed
    # assessment catalog independent of these ungraded taxonomy candidates.
    listing = (ROOT / "all-plants/index.html").read_text(encoding="utf-8")
    if "for(const c of catalog.rows){if(!c[5])continue;" not in listing:
        errors.append("Public catalog must exclude taxonomy-only species")
    page = PAGE.read_text(encoding="utf-8")
    # Entries without embedded evidence wait for the Batch 002 index before visibility is decided (non-blocking otherwise).
    if not re.search(r"if\(rec&&!directEvidence\)\{\s*batch002=await j\('\.\./data/catalog-evidence/batch-002-site-index\.json'\);", page)             or "batch002?.by_scientific_name?" not in page:
        errors.append("Batch 002 must load before detail-page evidence visibility check")
    if "Array.isArray(rec.feeding_evidence)&&rec.feeding_evidence.length" not in page:
        errors.append("Detail page must reject taxa without feeding records")
    for marker in ("batch002HTML(r)", "batch-002-site-index.json", "by_scientific_name", "reported_name", "source_key"):
        if marker not in page:
            errors.append(f"Site integration missing {marker}")
    print(json.dumps({
        "records": len(records), "unique_exact_reported_names": len(names),
        "held_not_linked": len(data.get("held_not_linked", [])),
        "sources": len(sources), "by_verification": by_verification,
        "errors": errors[:30], "error_count": len(errors)
    }, ensure_ascii=False, indent=2))
    return 1 if errors else 0

if __name__ == "__main__":
    sys.exit(main())
