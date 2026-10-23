#!/usr/bin/env python3
"""Promote explicitly reviewed plant evidence into the reviewed evidence batch read by the catalog builder.

Input: a JSON file {"records":[{"reviewed":true,"reviewer":"...","original_inspected":true,
"scientific":"Genus species","source_url":"https://...","citation":"...","tortoise":"Testudo ...",
"type":"wild_feeding_observation","locator":"Table 3, page 8","plant_part":{"ko":"잎","en":"leaves"},
"finding":{"ko":"...","en":"..."},"source_class":"peer_reviewed"}]}
(scripts/build_evidence_candidates.py writes drafts in this shape with "reviewed": false).

Only records a person approved after reading the original are accepted: reviewed and original_inspected true, a
reviewer name, an exact binomial, an http(s) source URL, a tortoise species, a locator, the plant part and the
finding in Korean and English, and for nutrition / toxicity the basis or test conditions. Record types are the
site's own (see TYPES); earlier names (captive_feeding_report, husbandry_guidance, nutritional_analysis,
toxicity_report) are mapped to them and the mapping is reported. Bibliography candidates are never promoted.

Output: data/catalog-evidence/reviewed-records.json (the batch-file schema; verification reviewed_source_record).
The Batch 002 site index is not touched: it must stay identical to the Batch 002 corpus (qa_batch_002_site.py).
Rebuild the catalog afterwards (scripts/build_plant_catalog_v1.py) so the list, detail pages and sitemap agree.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
TYPES = {"wild_feeding_observation", "captive_feeding_record", "husbandry_recommendation", "nutrition", "toxicity",
         "offered_not_eaten", "wild_diet_not_detected"}
LEGACY = {"captive_feeding_report": "captive_feeding_record", "husbandry_guidance": "husbandry_recommendation",
          "nutritional_analysis": "nutrition", "toxicity_report": "toxicity"}
SOURCE_CLASSES = {"peer_reviewed", "thesis", "zoo_guideline", "government", "vet", "book", "nutrition_db", "other"}
NUTRITION_BASIS = {"dry_matter", "as_fed", "unstated"}


def valid_url(url):
    p = urlparse(url)
    return p.scheme in ("http", "https") and bool(p.netloc) and not p.username and not p.password


def empty_batch():
    return {"schema_version": "1.0", "batch": "reviewed", "built": None,
            "corpus": {"id": "reviewed-records", "searched": None,
                       "summary": {"ko": "검토자가 원문을 읽고 승인한 기록입니다.", "en": "Records approved by a reviewer who read the original."}},
            "scope": "Reviewer-approved feeding, nutrition and toxicity records. A record is not a feeding grade.",
            "verification_levels": {"reviewed_source_record": "a reviewer read the original and approved the record"},
            "sources": [], "records": [], "held_not_linked": [], "sources_not_used": [], "reviewed_not_feeding_evidence": []}


def check(record):
    if record.get("reviewed") is not True or not str(record.get("reviewer", "")).strip():
        raise ValueError("explicit reviewer approval required")
    if record.get("original_inspected") is not True:
        raise ValueError("the reviewer must have read the original (original_inspected: true)")
    scientific = str(record.get("scientific") or "").strip()
    scientific = " ".join(scientific.split()[:2]) if re.fullmatch(r"[A-Z][a-z-]+ [a-z][a-z-]+(?: .*)?", scientific) else scientific
    if not re.fullmatch(r"[A-Z][a-z-]+ [a-z][a-z-]+", scientific):
        raise ValueError("exact binomial required")
    if not valid_url(str(record.get("source_url") or "")):
        raise ValueError("http(s) source URL required")
    typ = record.get("type")
    mapped = LEGACY.get(typ, typ)
    if mapped not in TYPES:
        raise ValueError(f"unsupported evidence type {typ!r}")
    if not re.match(r"[A-Z][a-z]+ [a-z]{3,}", str(record.get("tortoise") or "")):
        raise ValueError("tortoise species (binomial) required")
    for field in ("citation", "locator"):
        if len(str(record.get(field, "")).strip()) < 5:
            raise ValueError(field + " missing")
    for field in ("plant_part", "finding"):
        value = record.get(field)
        if not isinstance(value, dict) or not all(str(value.get(lang, "")).strip() for lang in ("ko", "en")):
            raise ValueError(field + " must contain ko and en")
    if mapped == "nutrition" and not ((record.get("nutrition") or {}).get("basis") in NUTRITION_BASIS and record["nutrition"].get("part")):
        raise ValueError("nutrition record needs nutrition.basis and nutrition.part")
    if mapped == "toxicity" and not ((record.get("toxicity") or {}).get("test_animal") and record["toxicity"].get("conditions")):
        raise ValueError("toxicity record needs toxicity.test_animal and toxicity.conditions")
    return scientific, mapped


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--approved", default="worker-output/approved-feeding-records.json")
    p.add_argument("--output", default=str(ROOT / "data/catalog-evidence/reviewed-records.json"))
    p.add_argument("--report", default="worker-output/promotion-report.json")
    args = p.parse_args()
    path = Path(args.approved)
    if not path.is_file():
        print("No approved records file; nothing published.")
        return
    records = json.loads(path.read_text(encoding="utf-8")).get("records", [])
    if not isinstance(records, list):
        raise ValueError("records must be an array")
    out = Path(args.output)
    batch = json.loads(out.read_text(encoding="utf-8")) if out.exists() else empty_batch()
    sources = {s["source_key"]: s for s in batch["sources"]}
    promoted, rejected, mapped_types = [], [], []
    for n, record in enumerate(records):
        try:
            scientific, typ = check(record)
            if typ != record["type"]:
                mapped_types.append({"record": n, "from": record["type"], "to": typ})
            url = str(record["source_url"])
            key = "reviewed_" + hashlib.sha256(url.encode()).hexdigest()[:16]
            if key in sources and sources[key]["url"] != url:
                raise ValueError("source key collision")
            sources.setdefault(key, {"source_key": key, "citation": record["citation"], "url": url,
                                     "language": record.get("language", "en"),
                                     "source_class": record.get("source_class") if record.get("source_class") in SOURCE_CLASSES else "other",
                                     "tortoise_taxon": record["tortoise"], "context": record.get("context", "wild"),
                                     "study_id": record.get("study_id") or key, "read": "reviewer-approved after reading the original",
                                     "collected_by": "reviewed-import"})
            entry = {"source_key": key, "reported_name": scientific, "tortoise": record["tortoise"], "type": typ,
                     "verification": "reviewed_source_record", "context": record.get("context", "wild"),
                     "locator": record["locator"], "plant_part": record["plant_part"], "finding": record["finding"],
                     "reviewer": record["reviewer"]}
            for k in ("nutrition", "toxicity"):
                if record.get(k):
                    entry[k] = record[k]
            if any(x["source_key"] == key and x["reported_name"] == scientific and x["type"] == typ and x["locator"] == entry["locator"]
                   for x in batch["records"]):
                continue
            batch["records"].append(entry)
            promoted.append({"scientific": scientific, "source": url, "type": typ})
        except (KeyError, ValueError, TypeError) as exc:
            rejected.append({"record": n, "reason": str(exc)})
    batch["sources"] = sorted(sources.values(), key=lambda x: x["source_key"])
    if promoted:
        import time
        batch["built"] = batch["corpus"]["searched"] = time.strftime("%Y-%m-%d")
        out.write_text(json.dumps(batch, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    report = {"promoted": len(promoted), "rejected": len(rejected), "type_names_mapped": mapped_types,
              "promoted_records": promoted, "rejections": rejected, "output": str(out),
              "next": "rebuild the catalog (scripts/build_plant_catalog_v1.py) and run scripts/qa_plant_catalog_v1.py",
              "warning": "Review approval must be based on original source inspection, not title/abstract matching."}
    dest = Path(args.report)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if rejected:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
