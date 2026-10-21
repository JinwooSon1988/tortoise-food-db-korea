"""Record-level audit of batch 002: recounts what the catalog actually carries and checks every batch record.

For each record: whether and how its printed name links to a catalog entry (exact GBIF name, GBIF synonym, orthographic
variant, or the reason it is not linked), the tortoise, plant part, verification level and evidence type; with the saved
agent texts (b2 dir, optional) also whether the quote is found again and whether the binomial is in the quote.
Writes docs/evidence-batch-002-audit-20261022.json. Nothing here creates or changes a feeding grade.
Run from the repository root: python -X utf8 scripts/evidence_corpus/batch_002/audit_batch_002.py [b2 dir]
"""
import json, re, sys, collections, unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
B2 = Path(sys.argv[1]) if len(sys.argv) > 1 else None
CHECKED = {"full_text_verified", "full_text_named_not_extracted", "review_full_text_verified", "guideline_full_text_verified"}
COMMUNITY = {"community_report_unverified", "video_observation_unverified"}
PRIORITY = {"sulcata": ["sulcata"], "leopard": ["pardalis", "babcocki"], "russian": ["horsfield"], "radiated": ["radiata"],
            "indian_star": ["elegans"], "burmese_star": ["platynota"]}


def norm(s):
    s = unicodedata.normalize("NFKC", s or ""); s = re.sub(r"-\s*\n\s*", "", s); s = s.replace("\xad", "")
    s = re.sub(r"[‘’“”`´]", "'", s); s = re.sub(r"[‐-―]", "-", s)
    return re.sub(r"\s+", " ", s).strip().casefold()


batch = json.loads((ROOT / "data/catalog-evidence/batch-002-20261021.json").read_text(encoding="utf-8"))
src = {s["source_key"]: s for s in batch["sources"]}
cit = {s["citation"]: k for k, s in src.items()}
index = json.loads((ROOT / "data/plant-catalog/index.json").read_text(encoding="utf-8"))
cat, linked = {}, collections.defaultdict(list)
for sh in index["shards"]:
    for e in json.loads((ROOT / "data/plant-catalog" / sh["file"]).read_text(encoding="utf-8"))["records"]:
        cat[e["id"]] = e
        for it in e.get("feeding_evidence") or []:
            if it["source"] in cit:
                linked[(cit[it["source"]], it["reported_name"], it["type"])].append((e["id"], e["scientific"], it))
reviewed = {p["scientific"].split(" (")[0] for p in json.loads((ROOT / "data/plants.json").read_text(encoding="utf-8"))}

# Saved texts: quote found again, binomial (or genus initial + epithet) inside the quote.
quote = {}
if B2:
    srows = {}
    for f in B2.glob("*/sources.jsonl"):
        for line in f.read_text(encoding="utf-8").splitlines():
            if line.strip():
                x = json.loads(line); srows[(f.parent.name, x["source_id"])] = x
    texts = {}
    OCR = json.loads((Path(__file__).parent / "b2_config.json").read_text(encoding="utf-8")).get("ocr_corrections", {})
    for line in (B2 / "verified.jsonl").read_text(encoding="utf-8").splitlines():
        v = json.loads(line)
        lt = v.get("local_txt") or srows.get((v["folder"], v["source_id"]), {}).get("local_txt")
        p = B2 / v["folder"] / lt if lt else None
        if not p or not p.exists():
            continue
        if p not in texts:
            texts[p] = norm(p.read_text(encoding="utf-8", errors="replace"))
        q, n = norm(v["quote"]), (v.get("plant_name_expanded") or v.get("plant_reported") or "").strip()
        ab = re.fullmatch(r"[A-Z]\. [a-z-]+ \(([A-Z][a-z-]+ [a-z-]+)\)", n)  # "A. minus (Alyssum minus)", as in make_batch_002
        n = OCR.get(ab.group(1) if ab else n, ab.group(1) if ab else n)
        w = q.split()
        found = q in texts[p] or bool(w) and all(" ".join(w[i:i + 6]) in texts[p] for i in range(0, max(1, len(w) - 5), 3))
        parts = n.split()
        n = " ".join(n.split()[:2])  # without the authority
        forms = {norm(n)} | ({norm(parts[0][0] + ". " + parts[1]), norm(parts[0][0] + "." + parts[1])} if len(parts) >= 2 else set())
        key = (v["source_id"], " ".join(parts[:2]))
        quote.setdefault(key, []).append({"found": found, "binomial_in_quote": any(f in q for f in forms)})

rows, by_status = [], collections.Counter()
for r in batch["records"]:
    k = (r["source_key"], r["reported_name"], r["type"])
    hits = linked.get(k, [])
    if hits:
        nr = hits[0][2].get("name_resolution")
        status = {"taxon_id": hits[0][0], "catalog_name": hits[0][1], "link": nr["basis"] if nr else "exact_gbif_name"}
    elif r["reported_name"] in reviewed:
        status = {"taxon_id": None, "link": "not_linked_reviewed_plant_page"}
    else:
        status = {"taxon_id": None, "link": "not_linked_no_exact_accepted_gbif_species_in_catalog"}
    by_status[status["link"]] += 1
    qc = quote.get((r["source_key"], r["reported_name"])) if B2 else None
    rows.append(dict(status, source_key=r["source_key"], study=src[r["source_key"]].get("study_id"), reported_name=r["reported_name"],
                     tortoise=r.get("tortoise"), type=r["type"], verification=r["verification"],
                     plant_part=(r.get("plant_part") or {}).get("en"), locator=r.get("locator"),
                     quote_found_again=None if qc is None else any(x["found"] for x in qc),
                     binomial_in_quote=None if qc is None else any(x["binomial_in_quote"] for x in qc)))

taxa = collections.defaultdict(list)
for k, hits in linked.items():
    for tid, _, it in hits:
        taxa[tid].append(it)
pri = {p: sorted({tid for tid, its in taxa.items() for it in its if any(s in (it.get("tortoise") or "").lower() for s in subs)})
       for p, subs in PRIORITY.items()}
summary = {
    "batch_file": {"sources": len(batch["sources"]), "records": len(batch["records"]), "held_not_linked": len(batch["held_not_linked"]),
                   "sources_not_used": len(batch["sources_not_used"]),
                   "records_by_verification": dict(collections.Counter(r["verification"] for r in batch["records"])),
                   "distinct_printed_names": len({r["reported_name"] for r in batch["records"]}),
                   "held_by_reason": dict(collections.Counter(h["reason"].split(":")[0] for h in batch["held_not_linked"]))},
    "catalog": {"taxa_with_batch_002_evidence": len(taxa),
                "taxa_with_batch_002_evidence_checked_in_an_original": sum(1 for its in taxa.values() if any(i["verification"] in CHECKED for i in its)),
                "taxa_with_only_community_or_video_batch_002_evidence": sum(1 for its in taxa.values() if all(i["verification"] in COMMUNITY for i in its)),
                "taxa_whose_only_evidence_is_batch_002": sum(1 for tid in taxa if all(i["source"] in cit for i in cat[tid]["feeding_evidence"])),
                "batch_002_evidence_items": sum(len(v) for v in taxa.values()),
                "items_by_verification": dict(collections.Counter(i["verification"] for its in taxa.values() for i in its)),
                "items_by_name_link": dict(collections.Counter((i.get("name_resolution") or {}).get("basis", "exact_gbif_name") for its in taxa.values() for i in its)),
                "safety_grades": sum(1 for e in cat.values() if e.get("safety_grade") is not None),
                "research_status": dict(collections.Counter(e["research"]["status"] for e in cat.values()))},
    "records_by_link": dict(by_status),
    "priority_tortoises_taxa": {p: len(v) for p, v in pri.items()},
    "quote_recheck": None if not B2 else {
        "records_checked": sum(1 for x in rows if x["quote_found_again"] is not None),
        "quote_found_again": sum(1 for x in rows if x["quote_found_again"]),
        "binomial_not_in_quote": [(x["source_key"], x["reported_name"]) for x in rows if x["quote_found_again"] and not x["binomial_in_quote"]]},
}
out = ROOT / "docs/evidence-batch-002-audit-20261022.json"
out.write_text(json.dumps({"schema_version": "1.0", "audited": "2026-10-22", "summary": summary, "records": rows}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False, indent=1))
