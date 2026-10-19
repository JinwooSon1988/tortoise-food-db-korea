#!/usr/bin/env python3
"""Inventory of every plant, source, feeding record, public evidence row, translation and image in the repository.

Run: python scripts/build_evidence_corpus_inventory.py   (writes data/evidence_corpus_inventory_20261019.json)

Collection only. Nothing here verifies a feeding record or a safety claim:
- sources are de-duplicated by normalised DOI (lower case, resolver prefix and trailing punctuation removed) or,
  without a DOI, by normalised URL;
- each source gets an evidence-level class from the fields already stored with it (directness, source type,
  animal taxon), not from reading the original;
- bibliographic leads and taxonomy candidates from the local discovery runs are counted as candidates and never
  merged into the reviewed sources.
The discovery/triage folders are local research data that are not tracked in git; when they are absent the
inventory records them as not present instead of failing.
"""
import json, re, subprocess, sys
from collections import defaultdict
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/evidence_corpus_inventory_20261019.json"
DOI_RE = re.compile(r"10\.\d{4,9}/[^\s\"<>|,;]+", re.I)
TORTOISE = re.compile(r"Testudo|Chersina|Centrochelys|Geochelone|Stigmochelys|Chelonoidis|Kinixys|Agrionemys|Astrochelys|"
                      r"Indotestudo|Gopherus|Homopus|Psammobates|Malacochersus|Manouria|Pyxis|tortoise", re.I)


def load(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def load_lenient(path):
    """Local triage files end with a literal backslash-n after the JSON document; read the document and report it."""
    text = path.read_text(encoding="utf-8")
    obj, end = json.JSONDecoder().raw_decode(text)
    return obj, text[end:].strip()


def norm_doi(s):
    s = unquote(str(s or "")).strip()
    m = DOI_RE.search(s)
    if not m:
        return None
    return m.group(0).rstrip(".)]}").lower()


def norm_url(s):
    s = str(s or "").strip()
    if not s.startswith(("http://", "https://")):
        return None
    u = urlsplit(s)
    return (u.netloc.lower().removeprefix("www.") + u.path.rstrip("/") + (("?" + u.query) if u.query else "")).lower()


def source_key(doi=None, url=None, fallback=None):
    d = norm_doi(doi) or norm_doi(url) or norm_doi(fallback)
    if d:
        return "doi:" + d
    u = norm_url(url) or norm_url(fallback)
    return "url:" + u if u else None


def level(directness, source_type, animal):
    animal = str(animal or "")
    tort = bool(TORTOISE.search(animal)) and "not tortoise" not in animal.lower()
    d = str(directness or "").lower()
    if d == "direct" and tort:
        return "direct_tortoise"
    if tort:
        return "indirect_tortoise"
    if "toxic" in str(source_type or "").lower() or "toxic" in animal.lower():
        return "toxicology_context"
    if d in ("contextual", "taxon_group", "indirect"):
        return "contextual_non_tortoise"
    return "unclassified"


def tracked_json():
    out = subprocess.run(["git", "ls-files", "data"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
    return [p for p in out if p.endswith(".json")]


def main():
    plants = load("data/plants.json")
    assessments = load("data/public_assessments.json")
    pub = load("data/public_evidence_records.json")["records"]
    links = load("data/plant_feeding_evidence_links.json")
    rev = load("data/reviewed_plant_reverse_evidence_index.json")["records"]
    wild = load("data/wild_feeding_evidence.json")["records"]
    ledger = load("data/feeding_record_verification_v1.json")
    extracts = load("data/feeding_record_fulltext_extracts_v1.json")
    images = load("data/verified_plant_images_v56.json")
    strings = load("data/i18n/en/strings_en.json")

    sources = {}

    def add(key, where, **info):
        if not key:
            return
        s = sources.setdefault(key, {"key": key, "occurrences": [], "plant_ids": set(), "titles": set(), "years": set(),
                                      "levels": set(), "animal_taxa": set(), "source_types": set(), "record_ids": set()})
        s["occurrences"].append(where)
        for f, k in (("plant_ids", "plant_ids"), ("titles", "title"), ("years", "year"), ("levels", "level"),
                     ("animal_taxa", "animal"), ("source_types", "source_type"), ("record_ids", "record_id")):
            v = info.get(k)
            if v in (None, "", []):
                continue
            s[f].update(v if isinstance(v, (list, set, tuple)) else [v])

    for r in pub:
        add(source_key(r.get("doi"), r.get("url")), f"public_evidence_records:{r['id']}", plant_ids=r["plant_ids"],
            title=r.get("source_title"), year=r.get("year"), animal=r.get("animal_taxon"), source_type=r.get("source_type"),
            record_id=r["id"], level=level(r.get("directness"), r.get("source_type"), r.get("animal_taxon")))
    for item in links["records"]:
        for e in item["evidence"]:
            add(source_key(None, e.get("source_id"), e.get("source_id")), f"plant_feeding_evidence_links:{item['plant_id']}:{e.get('evidence_id')}",
                plant_ids=[item["plant_id"]], animal=e.get("tortoise_taxon"), source_type=e.get("type"), record_id=e.get("evidence_id"),
                level=level(e.get("directness"), e.get("type"), e.get("tortoise_taxon")))
    for item in rev:
        for s in item["public_sources"] + item.get("wild_feeding_sources", []):
            add(source_key(None, s.get("url"), s.get("source_id")), f"reviewed_plant_reverse_evidence_index:{item['plant_id']}:{s.get('id')}",
                plant_ids=[item["plant_id"]], title=s.get("title"), animal=s.get("animal_taxon"), record_id=s.get("id"),
                level=level(s.get("directness"), None, s.get("animal_taxon")))
    for r in wild:
        add(source_key(None, r.get("source_id"), r.get("source_id")), f"wild_feeding_evidence:{r['id']}", plant_ids=[r["plant_id"]],
            animal=r.get("tortoise_taxon"), record_id=r["id"], level=level(r.get("directness"), "wild_feeding", r.get("tortoise_taxon")))
    for r in ledger["records"]:
        add(source_key(None, r.get("source"), r.get("source")), f"feeding_record_verification_v1:{r.get('plant_id') or r.get('candidate_taxon')}",
            plant_ids=[r["plant_id"]] if r.get("plant_id") else [], animal=r.get("tortoise_taxon"), source_type=r.get("source_type"))
    for s in extracts["sources"]:
        add(source_key(None, s.get("url"), s.get("source_key")), f"feeding_record_fulltext_extracts_v1:{s['source_key']}",
            animal=s.get("tortoise_taxon"), source_type=s.get("source_type"), level="direct_tortoise")

    # Every other tracked data file: DOIs anywhere in the text are counted as occurrences, never as evidence.
    generic_files = 0
    for rel in tracked_json():
        if rel in ("data/evidence_corpus_inventory_20261019.json", "data/source_access_check_20261019.json",
                   "data/evidence_conflict_audit_20261019.json"):
            continue
        text = (ROOT / rel).read_text(encoding="utf-8", errors="ignore")
        found = {norm_doi(m) for m in DOI_RE.findall(text)}
        found.discard(None)
        if found:
            generic_files += 1
        for d in found:
            if ("doi:" + d) in sources:
                if not any(o.startswith(rel[5:-5] + ":") or o == rel for o in sources["doi:" + d]["occurrences"]):
                    sources["doi:" + d]["occurrences"].append(rel)
            else:
                add("doi:" + d, rel)

    # Candidate pools from local discovery runs (untracked); counted, not merged.
    local = {}
    disc = ROOT / "data/original-source-discovery"
    local["original_source_discovery_files"] = sum(1 for _ in disc.glob("*.json")) if disc.exists() else None
    leads_p = ROOT / "data/original-source-summary/paper_leads.jsonl"
    leads = [json.loads(l) for l in leads_p.read_text(encoding="utf-8").splitlines() if l.strip()] if leads_p.exists() else []
    lead_keys = {}
    for l in leads:
        k = source_key(l.get("doi"), None) or ("epmc:" + str(l.get("source")) + ":" + str(l.get("record_id")))
        lead_keys.setdefault(k, l)
    local["bibliographic_leads"] = len(leads) if leads_p.exists() else None
    local["bibliographic_leads_unique"] = len(lead_keys) if leads_p.exists() else None
    local["bibliographic_leads_overlapping_reviewed_sources"] = sorted(k for k in lead_keys if k in sources)
    triage_dir = ROOT / "data/feeding-triage"
    shard_dir = ROOT / "data/evidence-review-shards"
    malformed, triage_n, triage_src, shard_n = [], 0, 0, 0
    for d in (triage_dir, shard_dir):
        if not d.exists():
            continue
        for p in sorted(d.glob("*.json")):
            obj, tail = load_lenient(p)
            if tail:
                malformed.append({"file": str(p.relative_to(ROOT)).replace("\\", "/"), "trailing_text": tail})
            for r in obj.get("records", []):
                if d == triage_dir:
                    triage_n += 1
                    triage_src += len(r.get("candidate_sources", []))
                else:
                    shard_n += 1
    local["feeding_triage_records"] = triage_n if triage_dir.exists() else None
    local["feeding_triage_candidate_sources"] = triage_src if triage_dir.exists() else None
    local["evidence_review_shard_records"] = shard_n if shard_dir.exists() else None
    local["malformed_local_files"] = malformed

    tax_n = 0
    for p in sorted((ROOT / "data/taxonomy-shards").glob("taxa-*.json")):
        tax_n += len(json.loads(p.read_text(encoding="utf-8")).get("records", []))
    eq = load("data/evidence-first-queue/index.json")
    eq_n = sum(len(load("data/evidence-first-queue/" + s["file"])["records"]) for s in eq["shards"])

    # Duplicate checks on the reviewed sources.
    dup_doi_ids = {k: sorted(v["record_ids"]) for k, v in sources.items()
                   if k.startswith("doi:") and len({i for i in v["record_ids"] if i and not str(i).startswith(("10.", "http"))}) > 1}
    doi_case_variants = defaultdict(set)
    for r in pub:
        if r.get("doi"):
            doi_case_variants[norm_doi(r["doi"])].add(r["doi"])
    doi_case_variants = {k: sorted(v) for k, v in doi_case_variants.items() if len(v) > 1}
    title_years = {k: {"titles": sorted(v["titles"]), "years": sorted(map(str, v["years"]))} for k, v in sources.items()
                   if len({str(y) for y in v["years"]}) > 1}

    src_list = []
    for k, v in sorted(sources.items()):
        src_list.append({"key": k, "levels": sorted(v["levels"]) or ["unclassified"], "plant_ids": sorted(v["plant_ids"]),
                         "record_ids": sorted(map(str, v["record_ids"])), "titles": sorted(v["titles"]),
                         "years": sorted(map(str, v["years"])), "animal_taxa": sorted(v["animal_taxa"]),
                         "source_types": sorted(v["source_types"]), "occurrence_count": len(v["occurrences"]),
                         "occurrences": sorted(set(v["occurrences"]))})
    by_level = defaultdict(int)
    for s in src_list:
        by_level[s["levels"][0] if len(s["levels"]) == 1 else "mixed:" + "+".join(s["levels"])] += 1

    counts = {
        "plants": len(plants), "public_assessments": len(assessments), "public_evidence_records": len(pub),
        "plant_feeding_evidence_link_rows": sum(len(i["evidence"]) for i in links["records"]),
        "quarantined_wild_records": len(links.get("quarantined_wild_records", [])),
        "reverse_index_public_source_rows": sum(len(i["public_sources"]) for i in rev),
        "wild_feeding_records": len(wild), "ledger_candidates": len(ledger["records"]),
        "fulltext_extract_sources": len(extracts["sources"]), "fulltext_extract_records": len(extracts["records"]),
        "verified_images": len(images["images"]), "rejected_image_candidates": len(images.get("rejected_candidates", [])),
        "translation_entries": len(strings), "taxonomy_candidates_tracked": tax_n, "evidence_first_queue": eq_n,
        "unique_sources": len(src_list), "unique_sources_with_doi": sum(s["key"].startswith("doi:") for s in src_list),
        "unique_sources_by_level": dict(sorted(by_level.items())),
        "tracked_data_files_with_doi": generic_files,
    }
    out = {"schema_version": "1.0", "built": "2026-10-19",
           "scope": "Inventory and de-duplication only. Levels are read from stored fields; no source here is verified by this file.",
           "counts": counts, "local_candidate_pools": local,
           "duplicates": {"same_doi_multiple_record_ids": dup_doi_ids, "doi_case_variants_in_public_records": doi_case_variants,
                          "same_source_multiple_years": title_years},
           "sources": src_list}
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({**counts, "local": {k: (v if not isinstance(v, list) else len(v)) for k, v in local.items()}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
