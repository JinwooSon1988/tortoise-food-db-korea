"""Batch 004 assembly: verified, deduplicated candidate records -> data/catalog-evidence/batch-004-YYYYMMDD.json.

A candidate becomes a record only if
  - its quote is re-found in the saved text rendering of the document (whitespace-normalised),
  - its name resolves in the GBIF Backbone the way the catalog builder links names (exact accepted, recorded synonym
    or spelling variant; see normalize.py), and it is not a P1-held claim,
  - the same plant x tortoise x source x record type is not already linked by batches 001-003 or the catalog.
Everything else is kept in held_not_linked with the reason. One record per plant x tortoise x source x type (table
rows preferred). verification = full_text_auto_extracted: the passage was found in an open full text by the
extractor and re-found by this script, but a person has not read it; it is never counted as "checked in the original".
Run: python -X utf8 -I assemble.py <repo root> <out json> <docs.jsonl> <extract dir> [<extract dir> ...]
"""
import gzip
import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(ROOT / "scripts"))
from build_plant_catalog_v1 import P1_HELD_CLAIMS, source_id  # noqa: E402

LEVEL = "full_text_auto_extracted"
FINDING = {
    ("wild_feeding_observation", "faecal"): ("분변 분석에서 먹은 식물로 확인되어 원문에 기록됨", "Recorded in the source as identified in faecal analysis"),
    ("wild_feeding_observation", "stomach"): ("위 내용물에서 확인되어 원문에 기록됨", "Recorded in the source as found in stomach contents"),
    ("wild_feeding_observation", "observed"): ("야생 개체가 먹은 식물로 원문에 기록됨", "Recorded in the source as eaten by wild tortoises"),
    ("captive_feeding_record", "captive"): ("사육 개체가 먹었거나 급여받은 식물로 원문에 기록됨", "Recorded in the source as eaten by or fed to captive tortoises"),
}
PART = {"leaf": ("잎", "leaf"), "flower": ("꽃", "flower"), "fruit": ("열매", "fruit"), "seed": ("씨앗", "seed"),
        "pad/cladode": ("줄기마디(패드)", "pad/cladode"), "stem": ("줄기", "stem"), "root": ("뿌리·덩이줄기", "root or tuber")}


def norm(s):
    s = unicodedata.normalize("NFKC", s or "")
    s = re.sub(r"[‐-―]", "-", s)
    return re.sub(r"\s+", " ", s).strip().casefold()


def species_of(t):
    m = re.match(r"([A-Z][a-z]+ [a-z]{3,})", str(t or ""))
    return m.group(1).lower() if m else str(t or "").strip().lower()


def main():
    out_json, docs_path, ext_dirs = Path(sys.argv[2]), Path(sys.argv[3]), [Path(p) for p in sys.argv[4:]]
    docs = {d["doc_id"]: d for d in map(json.loads, docs_path.read_text(encoding="utf-8").splitlines()) if d}
    linkable, name_reason = {}, {}
    for d in ext_dirs:
        if (d / "linkable_names.json").exists():
            linkable.update(json.loads((d / "linkable_names.json").read_text(encoding="utf-8")))
        if (d / "name_review.jsonl").exists():
            for r in map(json.loads, (d / "name_review.jsonl").read_text(encoding="utf-8").splitlines()):
                name_reason.setdefault(r["name"], r["reason"])
    cands = [dict(json.loads(l), _dir=str(d)) for d in ext_dirs for l in (d / "candidates.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]

    # what earlier batches and the catalog already link: (catalog key, tortoise species, source)
    existing = set()
    for f in sorted((ROOT / "data/plant-catalog").glob("taxa-*.json")):
        for r in json.loads(f.read_text(encoding="utf-8"))["records"]:
            k = r["id"].split(":")[1]
            for e in r["feeding_evidence"]:
                if e["verification"] == LEVEL:
                    continue  # this batch's own records from an earlier build are not "earlier batches"
                existing.add((k, species_of(e.get("tortoise")), source_id(e.get("url") or e.get("source"))))
    prior_sources = {}
    for f in sorted((ROOT / "data/catalog-evidence").glob("batch-[0-9][0-9][0-9]-*.json")):
        if "batch-004" in f.name:
            continue
        for s in json.loads(f.read_text(encoding="utf-8"))["sources"]:
            prior_sources[source_id(s.get("url"))] = s

    texts, held, kept = {}, [], {}
    counts = Counter()
    for c in cands:
        doc = docs.get(c["doc_id"])
        if not doc:
            counts["no_document"] += 1; continue
        src_url = ("https://doi.org/" + doc["doi"]) if doc.get("doi") and doc["kind"] == "jats" else (doc.get("url") or "")
        sid = source_id(src_url)
        base = {"reported_name": c["name"], "source_key": "b4_" + c["doc_id"], "tortoise": c["tortoise"], "scope": "record"}
        tpath = Path(c["_dir"]) / "text" / (c["doc_id"] + ".txt")
        if tpath not in texts:
            texts[tpath] = norm(tpath.read_text(encoding="utf-8")) if tpath.exists() else ""
        if not c.get("quote") or norm(c["quote"]) not in texts[tpath] or norm(c["printed"]) not in norm(c["quote"]):
            held.append(dict(base, reason="quote_not_refound")); counts["held_quote_not_refound"] += 1; continue
        key = linkable.get(c["name"])
        if not key:
            r = name_reason.get(c["name"], "name_not_checked")
            if r != "not_a_plant_genus":  # ordinary words caught by the binomial pattern are not recorded as held plants
                held.append(dict(base, reason="name_" + r))
            counts["held_name_" + r] += 1; continue
        if (c["name"], sid) in P1_HELD_CLAIMS:
            held.append(dict(base, reason="p1_identity_hold")); counts["held_p1"] += 1; continue
        if (key, species_of(c["tortoise"]), sid) in existing:
            counts["duplicate_of_earlier_batch"] += 1; continue
        ident = (key, species_of(c["tortoise"]), sid, c["type"])
        if ident in kept:
            counts["duplicate_within_batch"] += 1
            if c["unit_kind"] == "table_row" and kept[ident]["unit_kind"] != "table_row":
                kept[ident] = dict(c, _src=src_url, _sid=sid)
            continue
        kept[ident] = dict(c, _src=src_url, _sid=sid)

    # Every record must have a reviewer decision (the passage and its context read); undecided ones stay held.
    dpath = ROOT / "research/evidence-queue/batch-004/review_decisions.jsonl"
    decisions = {}
    if dpath.exists():
        for line in dpath.read_text(encoding="utf-8").splitlines():
            if line.strip():
                d = json.loads(line)
                decisions[(d["source_key"], d["reported_name"], d["tortoise"], d["type"])] = d
    undecided = []
    sources, records, quotes = {}, [], []
    for (key, _, sid, typ), c in sorted(kept.items(), key=lambda x: (x[1]["doc_id"], x[1]["name"])):
        doc = docs[c["doc_id"]]
        sk = "b4_" + c["doc_id"]
        d = decisions.get((sk, c["name"], c["tortoise"], typ))
        if not d or d["decision"] != "accept":
            reason = "not_reviewed" if not d else "reviewer_rejected: " + d.get("reason", "")
            held.append({"reported_name": c["name"], "source_key": sk, "tortoise": c["tortoise"], "scope": "record", "reason": reason})
            counts["held_not_reviewed" if not d else "held_reviewer_rejected"] += 1
            if not d:
                undecided.append({"source_key": sk, "reported_name": c["name"], "tortoise": c["tortoise"], "type": typ,
                                  "locator": c["locator"], "quote": c["quote"]})
            continue
        prior = prior_sources.get(sid)
        if sk not in sources:
            sources[sk] = {"source_key": sk, "citation": (prior or {}).get("citation") or doc["citation"], "url": c["_src"] or doc.get("url"),
                           "doi": doc.get("doi"), "language": (prior or {}).get("language"), "source_class": doc.get("source_class") or "other",
                           "tortoise_taxon": c["tortoise"], "context": "captive" if typ == "captive_feeding_record" else "wild",
                           "study_id": (prior or {}).get("study_id") or doc.get("earlier_source_id") or sk,
                           "read": doc.get("access") or "saved full text", "collected_by": "batch-004 automatic extraction",
                           "license": doc.get("license")}
        fko, fen = FINDING.get((typ, c["method"]), FINDING[("wild_feeding_observation", "observed")])
        part = PART.get(c.get("plant_part"))
        rec = {"source_key": sk, "reported_name": c["name"], "tortoise": c["tortoise"], "type": typ, "verification": LEVEL,
               "context": "captive" if typ == "captive_feeding_record" else "wild",
               "locator": c["locator"] + (" (table row)" if c["unit_kind"] == "table_row" and "table" not in c["locator"].lower() else ""),
               "plant_part": {"ko": part[0], "en": part[1]} if part else None, "finding": {"ko": fko, "en": fen}}
        if c.get("expanded"):
            rec["reported_as"] = c["printed"]
        records.append(rec)
        quotes.append({"source_key": sk, "reported_name": c["name"], "printed": c["printed"], "tortoise": c["tortoise"], "type": typ,
                       "locator": rec["locator"], "quote": c["quote"], "doc_id": c["doc_id"]})
        counts["linked_records"] += 1
    batch = {
        "schema_version": "1.0", "batch": "batch-004", "built": "2026-10-23",
        "corpus": {"id": "corpus-2026-10-23-b4", "searched": "2026-10-23",
                   "searches": [{"area": "Every full text saved by batches 001-003, reprocessed", "services": "Europe PMC JATS XML; batch 002-003 PDF text"},
                                {"area": "Europe PMC open-access subset: land tortoises x diet, faeces, herbivory, captivity, nutrition, toxicity",
                                 "services": "Europe PMC REST search (cursor paging) and fullTextXML"}],
                   "documents": len(docs), "documents_with_records": len(sources),
                   "summary": {"ko": "저장된 원문 전체와 Europe PMC 오픈액세스 원문에서 거북 섭식 문장·표에 함께 나온 학명을 자동 추출하고, 인용 문장을 원문에서 다시 찾은 기록만 연결했습니다. 사람이 읽기 전 단계입니다.",
                               "en": "Scientific names printed with tortoise feeding wording in sentences or diet tables of saved and newly fetched open full texts, extracted automatically; only records whose quoted passage was re-found are linked. Not yet read by a person."}},
        "scope": "Machine-extracted feeding records (not safety verdicts). One record = plant x tortoise taxon as printed x source x record type.",
        "verification_levels": {LEVEL: "the passage naming the plant next to tortoise feeding wording was found automatically in an open full text and re-found verbatim; not yet read by a person"},
        "sources": list(sources.values()), "records": records, "held_not_linked": held,
        "sources_not_used": [], "reviewed_not_feeding_evidence": [], "counts": dict(counts)}
    out_json.write_text(json.dumps(batch, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    # Verbatim quotes (<= 25 words each) for re-verification; kept with the research queue, not shown on pages.
    qdir = ROOT / "research/evidence-queue/batch-004"
    qdir.mkdir(parents=True, exist_ok=True)
    with gzip.open(qdir / "records_with_quotes.jsonl.gz", "wt", encoding="utf-8") as f:
        for q in quotes:
            f.write(json.dumps(q, ensure_ascii=False) + "\n")
    # Candidates still waiting for a reviewer decision (input for the next review round).
    (qdir / "undecided.jsonl").write_text(
        "".join(json.dumps(u, ensure_ascii=False) + "\n" for u in undecided), encoding="utf-8")
    print(json.dumps(dict(counts), ensure_ascii=False))


if __name__ == "__main__":
    main()
