"""Batch 004 report: species newly linked, records by type and verification, unlinked reasons and request failure rates.
Run: python -X utf8 -I report.py <repo root> <catalog index before (json)> <out json> <extract dir> [<extract dir> ...]
"""
import json
import sys
from collections import Counter
from pathlib import Path


def requests_stats(paths):
    c = Counter()
    for p in paths:
        if not p.exists():
            continue
        for line in p.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            if r["kind"] != "fetch":
                continue
            c["requests"] += 1
            if r.get("robots") == "disallowed":
                c["robots_disallowed"] += 1
            elif r.get("status") == 200:
                c["ok"] += 1
            elif r.get("will_retry"):
                c["retried"] += 1
            else:
                c["failed"] += 1
    c["failure_rate"] = round(c["failed"] / c["requests"], 4) if c["requests"] else 0
    return dict(c)


def main():
    root, before_path, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    dirs = [Path(p) for p in sys.argv[4:]]
    before = json.loads(before_path.read_text(encoding="utf-8"))
    after = json.loads((root / "data/plant-catalog/index.json").read_text(encoding="utf-8"))
    b4 = json.loads(next((root / "data/catalog-evidence").glob("batch-004-*.json")).read_text(encoding="utf-8"))
    linked_before, linked_b4, ver, typ, checked = set(), set(), Counter(), Counter(), 0
    for f in sorted((root / "data/plant-catalog").glob("taxa-*.json")):
        for r in json.loads(f.read_text(encoding="utf-8"))["records"]:
            ev = r["feeding_evidence"]
            if any(e["verification"] != "full_text_auto_extracted" for e in ev):
                linked_before.add(r["id"])
            if any(e["verification"] == "full_text_auto_extracted" for e in ev):
                linked_b4.add(r["id"])
            for e in ev:
                ver[e["verification"]] += 1; typ[e["type"]] += 1
    extract = Counter()
    for d in dirs:
        cp = d / "extract_checkpoint.jsonl"
        if cp.exists():
            for line in cp.read_text(encoding="utf-8").splitlines():
                r = json.loads(line)
                extract["documents"] += 1
                extract[r.get("skipped") or ("with_candidates" if r.get("candidates") else "no_candidates")] += 1
    rep = {
        "catalog_entries": {"before": before["count"], "after": after["count"]},
        "species_with_feeding_evidence": {"before": before["counts"]["with_feeding_evidence"], "after": after["counts"]["with_feeding_evidence"],
                                          "increase": after["counts"]["with_feeding_evidence"] - before["counts"]["with_feeding_evidence"]},
        "species_linked_only_by_batch_004": len(linked_b4 - linked_before),
        "species_with_batch_004_records": len(linked_b4),
        "batch_004_records": len(b4["records"]), "batch_004_sources": len(b4["sources"]),
        "batch_004_records_by_type": dict(Counter(r["type"] for r in b4["records"])),
        "batch_004_held_by_reason": dict(Counter(h["reason"] for h in b4["held_not_linked"])),
        "batch_004_assembly_counts": b4.get("counts"),
        "catalog_records_by_verification": dict(ver), "catalog_records_by_type": dict(typ),
        "checked_in_original_records": sum(v for k, v in ver.items() if k in ("full_text_verified", "review_full_text_verified", "guideline_full_text_verified", "full_text_named_not_extracted")),
        "documents": dict(extract),
        "requests": {"gbif": requests_stats([d / "gbif_requests.jsonl" for d in dirs]),
                     "europe_pmc": requests_stats([d / "requests.jsonl" for d in dirs])},
        "unlinked_evidence_names": after.get("evidence_names_not_linked"),
    }
    out.write_text(json.dumps(rep, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(rep, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
