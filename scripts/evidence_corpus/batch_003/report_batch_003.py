"""Batch 003 figures: work queue, search, full-text, verification, site linkage, holds, duplicates, evidence types, gain.
Reads the repository (batch file, catalog, the catalog before this batch via git) and, when given, the queue folder and
the make_batch_003 stats line. Writes docs/evidence-batch-003-report-20261022.json.
Run from the repository root:
  python -X utf8 scripts/evidence_corpus/batch_003/report_batch_003.py <queue dir> <make_batch stats json> <git ref of the catalog before>
"""
import json, re, sys, subprocess, collections
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
Q, STATS, BEFORE = Path(sys.argv[1]), json.loads(Path(sys.argv[2]).read_text(encoding="utf-8")), sys.argv[3]
CHECKED = {"full_text_verified", "full_text_named_not_extracted", "review_full_text_verified", "guideline_full_text_verified"}
COMMUNITY = {"community_report_unverified", "video_observation_unverified"}


def catalog(ref=None):
    read = (lambda p: subprocess.run(["git", "show", f"{ref}:{p}"], cwd=ROOT, capture_output=True, check=True).stdout.decode("utf-8")) if ref \
        else (lambda p: (ROOT / p).read_text(encoding="utf-8"))
    out = {}
    for sh in json.loads(read("data/plant-catalog/index.json"))["shards"]:
        for e in json.loads(read("data/plant-catalog/" + sh["file"]))["records"]:
            out[e["id"]] = e
    return out


now, before = catalog(), catalog(BEFORE)
batch = json.loads((ROOT / "data/catalog-evidence/batch-003-20261022.json").read_text(encoding="utf-8"))
cits = {s["citation"] for s in batch["sources"]}
b3 = {t: [i for i in e.get("feeding_evidence") or [] if i["source"] in cits] for t, e in now.items()}
b3 = {t: v for t, v in b3.items() if v}
qr = [json.loads(l) for l in (Q / "queue_results.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
log = (Q / "queue_log.txt").read_text(encoding="utf-8").splitlines()
retries = max([int(m.group(1)) for l in log for m in [re.search(r"retry=(\d+)", l)] if m] or [0])
failed = sum(1 for l in (Q / "queue_failed.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()) if (Q / "queue_failed.jsonl").exists() else 0
mentions = [json.loads(l) for l in (Q / "mentions.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
ev = lambda c: {t for t, e in c.items() if e.get("feeding_evidence")}
chk = lambda c: {t for t, e in c.items() if any(i["verification"] in CHECKED for i in e.get("feeding_evidence") or [])}
report = {
    "batch": "batch-003", "built": batch["built"],
    "work_queue": {
        "catalog_species_at_start": len(before), "queued": len(before), "processed": len(qr), "not_processed": len(before) - len(qr),
        "failed_after_retries": failed, "retries": retries,
        "stopped": "the queue process was stopped by the host when the computer ran low on memory; it is restartable from queue_results.jsonl"
                   if len(qr) < len(before) else None},
    "search": {"species_searched_europe_pmc": len(qr), "species_with_hits": sum(1 for r in qr if r["hit_count"]),
               "total_hits": sum(r["hit_count"] for r in qr),
               "open_access_full_texts_scanned": len({m["pmcid"] for m in mentions if m.get("pmcid")}),
               "species_named_in_an_open_full_text": len({m["taxon_id"] for m in mentions if m.get("text")}),
               "species_named_next_to_a_tortoise_and_feeding_words": len({m["taxon_id"] for m in mentions if m.get("text") and m["tortoise_near"] and m["feeding_near"]}),
               "europe_pmc_records_accepted_after_reading": sum(1 for r in batch["records"] if r["source_key"].startswith("epmc_"))},
    "documents": {"read_and_saved": batch["corpus"]["documents_read"], "sources_with_records": len(batch["sources"]),
                  "leads_not_accessed": batch["corpus"]["leads_not_accessed"]},
    "records": {"in_batch": len(batch["records"]), "held_not_linked": len(batch["held_not_linked"]),
                "held_by_reason": dict(collections.Counter(h["reason"].split(":")[0] for h in batch["held_not_linked"])),
                "by_verification": dict(collections.Counter(r["verification"] for r in batch["records"])),
                "by_type": dict(collections.Counter(r["type"] for r in batch["records"]))},
    "duplicates": {"same_record_dropped": STATS.get("duplicate_dropped", 0), "already_linked_from_same_study": STATS.get("already_linked_from_same_study", 0),
                   "note": "TFTSG species accounts read by two agents were merged by source key"},
    "species": {
        "with_batch_003_evidence": len(b3),
        "with_batch_003_evidence_checked_in_an_original_or_review": sum(1 for v in b3.values() if any(i["verification"] in CHECKED for i in v)),
        "with_batch_003_evidence_checked_in_an_original_only": sum(1 for v in b3.values() if any(i["verification"] == "full_text_verified" for i in v)),
        "with_only_abstract_or_community_batch_003_evidence": sum(1 for v in b3.values() if not any(i["verification"] in CHECKED for i in v)),
        "new_catalog_entries": len(set(now) - set(before)),
        "newly_with_any_evidence": len(ev(now) - ev(before)),
        "newly_checked_in_full_text": len(chk(now) - chk(before))},
    "catalog": {"before": {"entries": len(before), "with_evidence": len(ev(before)), "checked_in_full_text": len(chk(before))},
                "after": {"entries": len(now), "with_evidence": len(ev(now)), "checked_in_full_text": len(chk(now))},
                "safety_grades_after": sum(1 for e in now.values() if e.get("safety_grade") is not None),
                "no_record_found_after": sum(1 for e in now.values() if e["research"]["status"] == "no_record_found")},
}
out = ROOT / "docs/evidence-batch-003-report-20261022.json"
out.write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=1))
