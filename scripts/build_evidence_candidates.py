#!/usr/bin/env python3
"""Offline evidence candidates from every local text: scientific names and synonyms linked to catalog or reviewed
plants, classified by evidence type, and split into "ready for a reviewer" and "needs human review".

Inputs (all local; no network, so it runs during any API cooldown):
  --bibliography  worker-output/worldwide-literature.json (titles and abstracts), if present
  --docs          one or more docs.jsonl lists of saved full texts (scripts/evidence_corpus/batch_004/make_docs.py)
  --gbif-cache    optional evidence_match.json (GBIF name matches cached by the catalog builder)
Names resolve to a taxon by: exact catalog name; a synonym or spelling variant already recorded in the catalog
(name_resolution of linked evidence); a cached GBIF match (exact, recorded synonym or spelling variant, as the
builder links names); or a reviewed plant (data/plants.json, also through its taxonomy note).

Evidence classes (one per text unit and name):
  name_mention          the name appears without tortoise feeding wording
  ingestion_observation tortoises eating it in the wild (observation, faeces, stomach contents)
  captive_feeding       fed to or eaten by captive tortoises
  toxicity_or_nutrition toxicity or nutrient wording
  not_eaten_or_avoided  negated or avoidance wording
"ready_for_reviewer" needs all of: ingestion_observation or captive_feeding from a full text (not a title or
abstract), a tortoise species named in the source, a plant part stated next to the name, an http(s) source URL, the
quoted passage re-found in the saved text, and no P1 hold or earlier record for the same plant, tortoise and source.
Nothing here is promoted: ready candidates are written as approval drafts with "reviewed": false, which a person
sets after reading the original (scripts/promote_reviewed_feeding_evidence.py rejects anything else).
"""
import argparse
import glob
import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts/evidence_corpus/batch_004"))
from build_plant_catalog_v1 import P1_HELD_CLAIMS, resolve, source_id  # noqa: E402
import extract as ex  # noqa: E402

TOXNUT = re.compile(r"\b(toxic\w*|\w*toxins?|poison\w*|intoxicat\w*|oxalat\w*|alkaloids?|saponins?|glycosides?|nitrogen|crude\s+protein|"
                    r"nutrient\w*|calcium|phosphorus|fib(?:re|er)|digestib\w*|energy\s+content|proximate)\b", re.I)
READY_CLASSES = {"ingestion_observation", "captive_feeding"}


def norm(s):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", s or "")).strip().casefold()


def taxon_index(gbif_cache):
    """name (casefold) -> (target id, scientific, basis); target id is gbif:<key> or plant:<reviewed id>."""
    idx, by_key = {}, {}
    for f in sorted((ROOT / "data/plant-catalog").glob("taxa-*.json")):
        for r in json.loads(f.read_text(encoding="utf-8"))["records"]:
            by_key[r["id"].split(":")[1]] = r
            idx[r["scientific"].casefold()] = (r["id"], r["scientific"], "exact")
            for e in r["feeding_evidence"]:
                nr = e.get("name_resolution")
                if nr and nr.get("reported"):
                    idx.setdefault(nr["reported"].casefold(), (r["id"], r["scientific"], nr["basis"]))
    for p in json.loads((ROOT / "data/plants.json").read_text(encoding="utf-8")):
        names = re.findall(r"\b([A-Z][a-z]+ [a-z][a-z-]+)\b", (p.get("scientific") or "") + " " + (p.get("taxonomy_note") or ""))
        for n in names:
            idx.setdefault(n.casefold(), ("plant:" + p["id"], p["scientific"], "reviewed_plant"))
    if gbif_cache and Path(gbif_cache).exists():
        for n, m in json.loads(Path(gbif_cache).read_text(encoding="utf-8")).items():
            key, basis = resolve(n, m or {})
            if key and key in by_key and n.casefold() not in idx:
                idx[n.casefold()] = (by_key[key]["id"], by_key[key]["scientific"], basis or "exact")
    return idx


def squash(s):
    """First 40 letters/digits of a citation (authors and year), to match one work cited in different styles."""
    return re.sub(r"[^0-9a-z]", "", str(s or "").lower())[:40]


def species_of(t):
    """Tortoise species key: genus initial + epithet, so "T. graeca" and "Testudo graeca" compare equal."""
    m = re.search(r"\b([A-Z])(?:[a-z]+|\.)\s*([a-z]{3,})\b", str(t or ""))
    return (m.group(1) + " " + m.group(2)).lower() if m else None


def readiness(c, held):
    """What a candidate still lacks before a reviewer can approve it (empty list = ready)."""
    missing = []
    if c["evidence_class"] not in READY_CLASSES:
        missing.append("evidence class " + c["evidence_class"])
    if not c["full_text"]:
        missing.append("full text (title or abstract only)")
    if not species_of(c["tortoise"]):
        missing.append("tortoise species")
    if not c["plant_part"]:
        missing.append("plant part")
    if not str(c.get("url") or "").startswith("http"):
        missing.append("source URL")
    if c["full_text"] and not c.get("quote_refound"):
        missing.append("quote re-found in the saved text")
    if c["reported_name"] in held:
        missing.append("name held in an earlier batch (identity doubt)")
    return missing


LOCATOR_GENERIC = {"title", "abstract", "body text"}


def completeness(c):
    """Sort key among duplicates: a full text over a title or abstract, then a re-found quote, a stated plant part,
    a specific locator (table or page over a section over title/abstract/body text), fewer missing items."""
    loc = str(c.get("locator") or "")
    specific = 2 if re.search(r"(?i)\b(table|tabla|tabela|fig(?:ure)?\.?|p\.\s*\d|page)\b", loc) else 0 if loc in LOCATOR_GENERIC or not loc else 1
    return (bool(c["full_text"]), bool(c.get("quote_refound")), bool(c["plant_part"]), specific, -len(c["missing"]))


def prior_reviews(base):
    """(doc_id, reported name, evidence class) -> decision from <base>/reviewed-*/review-decisions.jsonl."""
    out = {}
    for f in sorted(Path(base).glob("reviewed-*/review-decisions.jsonl")):
        for line in f.read_text(encoding="utf-8").splitlines():
            if line.strip():
                d = json.loads(line)
                out[(d["doc_id"], d["reported_name"], d["evidence_class"])] = {k: d.get(k) for k in ("decision", "reason", "reviewed", "reviewer")}
    return out


def held_names():
    """Names held as names in earlier batches (doubtful GBIF synonym or other identity doubt): never linkable here."""
    out = set()
    for f in sorted((ROOT / "data/catalog-evidence").glob("batch-*.json")):
        if "index" in f.name:
            continue
        for h in json.loads(f.read_text(encoding="utf-8")).get("held_not_linked", []):
            if h.get("scope", "name") == "name" or "synonym" in str(h.get("reason")) or "identity" in str(h.get("reason")):
                out.add(str(h.get("reported_name") or "").strip())
    return out


def classify(text, caption=""):
    ctx = text + " " + (caption or "")
    if ex.NEG.search(ctx) and not TOXNUT.search(ctx):
        return "not_eaten_or_avoided"
    if TOXNUT.search(ctx):
        return "toxicity_or_nutrition"
    if not ex.STRONG_FEED.search(ctx):
        return "name_mention"
    if ex.CAPTIVE.search(ctx):
        return "captive_feeding"
    return "ingestion_observation"


def scan_units(units, doc, idx, full_text, tort_hint=None):
    """Yield candidate dicts for every name in every unit."""
    tort_doc, _ = ex.doc_tortoise(units, tort_hint)
    for u in units:
        t, cap = u["text"], u.get("caption") or ""
        if u["kind"] == "table_row" and doc.get("kind") != "jats":
            continue
        tort_here = bool(ex.TORT_WORD.search(t) or ex.TORT_RE.search(t))
        unit_tort = next((m.group(1) + " " + m.group(2) for m in ex.TORT_RE.finditer(t + " " + cap) if m.group(2) not in ex.STOP_EPITHET), None)
        for m in ex.BINOMIAL.finditer(t):
            g, ep = m.group(1), m.group(3)
            name = g + " " + ep
            hit = idx.get(name.casefold())
            if not hit or g in ex.TORTOISE_GENERA:
                continue
            cls = classify(t, cap)
            if cls in READY_CLASSES and not (tort_here or ex.DIET_WORD.search(t) or u["kind"] == "table_row"):
                cls = "name_mention"
            if ex.OTHER_USE.search(t) and cls in READY_CLASSES:
                cls = "name_mention"
            yield {"target": hit[0], "scientific": hit[1], "name_basis": hit[2], "reported_name": name,
                   "evidence_class": cls, "tortoise": unit_tort or tort_doc, "plant_part": ex.part_near(t, m.span()),
                   "locator": u["locator"], "unit_kind": u["kind"], "quote": ex.quote_for(t, m.span()), "full_text": full_text}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bibliography", default="worker-output/worldwide-literature.json")
    ap.add_argument("--docs", nargs="*", default=[])
    ap.add_argument("--gbif-cache")
    ap.add_argument("--output", default="worker-output/evidence-candidates.json")
    ap.add_argument("--drafts", default="worker-output/approval-drafts.json")
    ap.add_argument("--reviews-dir", default=str(ROOT / "research/evidence-queue"), help="folder with reviewed-*/review-decisions.jsonl")
    a = ap.parse_args()
    idx = taxon_index(a.gbif_cache)
    held = held_names()
    links, no_evidence = set(), set()
    for f in sorted((ROOT / "data/plant-catalog").glob("taxa-*.json")):
        for r in json.loads(f.read_text(encoding="utf-8"))["records"]:
            if not r["feeding_evidence"]:
                no_evidence.add(r["id"])
            for e in r["feeding_evidence"]:
                links.add((r["id"], species_of(e.get("tortoise")), source_id(e.get("url") or e.get("source"))))
                # the same work can be cited by DOI in one batch and by its PDF URL in another
                links.add((r["id"], species_of(e.get("tortoise")), "cite:" + squash(e.get("source"))))
    out, counts, docs_seen = [], Counter(), 0

    bib = Path(a.bibliography)
    if bib.exists():
        for w in json.loads(bib.read_text(encoding="utf-8")).get("works", []):
            docs_seen += 1
            doc = {"doc_id": str(w.get("openalex_id") or w.get("id") or w.get("doi")), "kind": "bibliography",
                   "citation": w.get("title"), "url": w.get("doi") or w.get("url"), "doi": w.get("doi")}
            units = [{"text": s, "locator": field, "kind": "sentence"} for field in ("title", "abstract")
                     for s in re.split(r"(?<=[.!?])\s+", str(w.get(field) or "")) if s]
            for c in scan_units(units, doc, idx, full_text=False):
                out.append(dict(c, doc_id=doc["doc_id"], citation=doc["citation"], url=doc["url"], source="bibliography"))
    for dl in a.docs:
        for line in Path(dl).read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            doc = json.loads(line)
            p = Path(doc["path"])
            if not p.exists() or doc.get("source_class") not in ex.AUTO_CLASSES:
                counts["documents_skipped"] += 1
                continue
            docs_seen += 1
            units = ex.jats_units(p) if doc["kind"] == "jats" else ex.txt_units(p)
            whole = norm(" ".join(u["text"] for u in units))
            for c in scan_units(units, doc, idx, full_text=True, tort_hint=doc.get("tortoise_hint")):
                url = ("https://doi.org/" + doc["doi"]) if doc.get("doi") else doc.get("url")
                out.append(dict(c, doc_id=doc["doc_id"], citation=doc.get("citation"), url=url, source="full_text",
                                quote_refound=norm(c["quote"]) in whole))

    # Readiness first, then de-duplication: one candidate per target x tortoise x source x class, keeping the most
    # complete one (see completeness()); a candidate without a tortoise species is a duplicate when the same target,
    # source and class also has one with a species. Earlier review decisions are carried over, never re-queued.
    prior = prior_reviews(a.reviews_dir)
    for c in out:
        c["sid"] = source_id(c.get("url"))
        c["missing"] = readiness(c, held)
    groups = {}
    for c in out:
        groups.setdefault((c["target"], species_of(c["tortoise"]), c["sid"], c["evidence_class"]), []).append(c)
    with_species = {(t, s, k) for (t, sp, s, k) in groups if sp}
    best = []
    for key, items in groups.items():
        if key[1] is None and (key[0], key[2], key[3]) in with_species:
            counts["duplicate_candidates"] += len(items)
            counts["duplicate_without_tortoise_species"] += len(items)
            continue
        items.sort(key=completeness, reverse=True)
        keep = items[0]
        keep["alternate_locators"] = sorted({x["locator"] for x in items[1:] if x["locator"] != keep["locator"]})[:10]
        counts["duplicate_candidates"] += len(items) - 1
        if any(not x["full_text"] for x in items[1:]) and keep["full_text"]:
            counts["duplicate_full_text_preferred"] += 1
        best.append(keep)
    final = []
    for c in best:
        sid, missing = c.pop("sid"), c["missing"]
        if (c["reported_name"], sid) in P1_HELD_CLAIMS:
            missing.append("P1 identity hold")
        if ((c["target"], species_of(c["tortoise"]), sid) in links
                or (c["target"], species_of(c["tortoise"]), "cite:" + squash(c.get("citation"))) in links):
            c["already_linked"] = True
            counts["already_linked"] += 1
            continue
        decision = prior.get((c["doc_id"], c["reported_name"], c["evidence_class"]))
        if decision:
            c["prior_review"] = decision  # kept as decided; a rescan never re-queues or re-approves it
            c["state"] = "previously_reviewed"
        else:
            c["state"] = "ready_for_reviewer" if not missing else "needs_human_review"
        c["verified_feeding_evidence"] = False
        counts[c["state"]] += 1
        counts["class_" + c["evidence_class"]] += 1
        final.append(c)
    drafts = [{"reviewed": False, "reviewer": "", "original_inspected": False, "scientific": c["scientific"],
               "reported_name": c["reported_name"], "source_url": c["url"], "citation": c.get("citation") or "",
               "tortoise": c["tortoise"], "type": "captive_feeding_record" if c["evidence_class"] == "captive_feeding" else "wild_feeding_observation",
               "context": "captive" if c["evidence_class"] == "captive_feeding" else "wild", "locator": c["locator"],
               "plant_part": {"ko": ex_part_ko(c["plant_part"]), "en": c["plant_part"]}, "finding": {"ko": "", "en": ""},
               "quote": c["quote"], "source_class": "peer_reviewed"}
              for c in final if c["state"] == "ready_for_reviewer"]
    summary = {"documents_scanned": docs_seen, "names_indexed": len(idx), "candidates": len(final),
               "targets": len({c["target"] for c in final}),
               "targets_ready_for_reviewer": len({c["target"] for c in final if c["state"] == "ready_for_reviewer"}),
               "catalog_targets": len({c["target"] for c in final if c["target"].startswith("gbif:")}),
               "catalog_targets_without_evidence": len({c["target"] for c in final if c["target"] in no_evidence}),
               "catalog_targets_without_evidence_ready": len({c["target"] for c in final
                                                             if c["target"] in no_evidence and c["state"] == "ready_for_reviewer"}),
               "counts": dict(counts),
               "warning": "Candidates are unverified. A ready candidate still needs a person to read the original before promotion."}
    for path, data in ((a.output, dict(summary, candidates=final)), (a.drafts, {"note": summary["warning"], "records": drafts})):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=1))


def ex_part_ko(part):
    return {"leaf": "잎", "flower": "꽃", "fruit": "열매", "seed": "씨앗", "pad/cladode": "줄기마디(패드)", "stem": "줄기",
            "root": "뿌리·덩이줄기"}.get(part or "", "")


if __name__ == "__main__":
    main()
