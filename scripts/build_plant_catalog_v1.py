#!/usr/bin/env python3
"""Build the searchable plant catalog (data/plant-catalog/) from GBIF-verified taxa.

Run: python scripts/build_plant_catalog_v1.py --gbif-dir <dir> --max 2000 [--batch-label batch-01]

<dir> holds the GBIF lookups made for this build (not committed; data from api.gbif.org):
  species.jsonl      one /v1/species/{key} record per candidate key
  vernacular.jsonl   English and Korean vernacular names per key
  existing_match.json  /v1/species/match results for the names in data/plants.json
  evidence_match.json  /v1/species/match results for plant names in feeding sources (written here if missing)

Candidates: the 9,995 tracked taxonomy candidates (data/taxonomy-shards/) and the 12,009 in
data/diverse_taxonomy_candidates.json, in that order, plus species named in feeding sources.
A catalog entry needs a GBIF record that is ACCEPTED, rank SPECIES, kingdom Plantae, whose canonical name equals
the candidate name; anything else is rejected with a reason. Plants already in data/plants.json (by name without
authors, or by GBIF usage/accepted/species key of an exact match) are not added again.

Taxonomy and feeding evidence are separate. Being a valid taxon is never feeding evidence. Every entry has
feeding_safety_status "unassessed" (급여 안전성 미확정) and no A-D grade. Feeding evidence is attached only from
repository sources, by type, and only where the reported name is an exact accepted GBIF species.

--max caps the number of entries (batches are appended in candidate order; earlier entries are kept).
"""
import argparse, hashlib, json, re, sys, urllib.parse, urllib.request
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/plant-catalog"
LOG = ROOT / "data/plant_catalog_batches_v1.json"
SHARDS = 40
CHECKED = "2026-10-20"
sys.path.insert(0, str(ROOT / "scripts"))
from build_bulk_taxon_catalog import bare  # noqa: E402

# El Mouden et al. 2006 names whose catalog linkage is held by the P1 release gate.
P1_HELD_NAMES = {"Leontodon saxatilis", "Malva parviflora", "Astragalus cruciatus", "Medicago hispida", "Lotus arenarius"}
EVIDENCE_TYPES = ("wild_feeding_observation", "captive_feeding_record", "husbandry_recommendation", "nutrition", "toxicity")


def load(p):
    return json.loads((ROOT / p).read_text(encoding="utf-8"))


def jsonl(p):
    out = {}
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                out[str(r["_key"])] = r
    return out


def gbif_match(names, cache_path):
    cache = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.exists() else {}
    for n in sorted(set(names) - set(cache)):
        u = "https://api.gbif.org/v1/species/match?" + urllib.parse.urlencode({"name": n, "kingdom": "Plantae", "strict": "true"})
        with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "geobukbap-taxonomy-check/1.0"}), timeout=30) as r:
            d = json.load(r)
        cache[n] = {k: d.get(k) for k in ("usageKey", "acceptedUsageKey", "canonicalName", "rank", "status", "matchType", "note")}
    cache_path.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
    return cache


def evidence_sources():
    """(reported name, evidence item) pairs from repository sources, by type. Nothing here is a safety verdict."""
    items = []
    t2 = load("data/elmouden2006_table2_verification_20261020.json")
    cite = "El Mouden et al. 2006, J. Arid Environ. 64:422-435"
    for r in t2["table_2"]["rows"]:
        name = r["taxon"]
        if not re.fullmatch(r"[A-Z][a-z]+ [a-z][a-z-]+", name):
            continue
        n, pct = r["occurrence_faeces_of_44"], r["faecal_mean_pct_of_fragments"]["mean"]
        base = {"type": "wild_feeding_observation", "tortoise": "Testudo graeca graeca", "source": cite,
                "url": "https://doi.org/10.1016/j.jaridenv.2005.06.010", "locator": "Table 2, p. %d" % r["page"],
                "verification": "full_text_verified", "plant_part": None, "context": "wild"}
        if n:
            items.append((name, dict(base, finding={
                "ko": "야생 개체 분변 44개 중 %d개에서 검출, 식별된 분변 조각의 평균 %s%% (모로코 중부, 2002년 봄)" % (n, pct),
                "en": "Found in %d of 44 faeces of wild tortoises, mean %s%% of identified faecal fragments (central Morocco, spring 2002)" % (n, pct)})))
        else:
            items.append((name, dict(base, type="wild_diet_not_detected", finding={
                "ko": "서식지에 있었으나 야생 개체 분변 44개에서 검출되지 않음 (모로코 중부, 2002년 봄)",
                "en": "Present in the habitat but not found in 44 faeces of wild tortoises (central Morocco, spring 2002)"})))
    ext = load("data/feeding_record_fulltext_extracts_v1.json")
    src = {s["source_key"]: s for s in ext["sources"]}
    for r in ext["records"]:
        s = src[r["source_key"]]
        items.append((r["plant_taxon_reported"], {
            "type": "wild_feeding_observation", "tortoise": (r.get("tortoise") or {}).get("taxon") or s["tortoise_taxon"],
            "source": s["citation"], "url": s["url"], "locator": s["sites"][r["site"]]["locator"],
            "verification": "full_text_verified", "context": s["context"],
            "plant_part": r["plant_part"] and {"ko": r["plant_part"]["ko"], "en": r["plant_part"]["en"]},
            "finding": r["observed"] and {"ko": r["observed"]["ko"], "en": r["observed"]["en"]}}))
    named = ext["species_in_full_text_not_in_catalog"]
    for key, names in named.items():
        if key in src and isinstance(names, list):
            s = src[key]
            for n in names:
                items.append((n, {"type": "wild_feeding_observation", "tortoise": s["tortoise_taxon"], "source": s["citation"],
                                  "url": s["url"], "locator": None, "verification": "full_text_named_not_extracted",
                                  "context": s["context"], "plant_part": None, "finding": None}))
    for f in sorted((ROOT / "research/evidence_leads").glob("*.json")):
        for r in json.loads(f.read_text(encoding="utf-8"))["records"]:
            names = r.get("observed_plant_taxa") or r.get("plant_taxa") or []
            kind = r.get("evidence_directness") or ""
            typ = "captive_feeding_record" if "captive" in kind else "wild_feeding_observation"
            for n in names:
                items.append((n, {"type": typ, "tortoise": r.get("animal_taxon"), "source": r.get("source_title") or r.get("id") or r.get("source_id"),
                                  "url": r.get("url") or r.get("source_url") or ("https://doi.org/" + r["doi"] if r.get("doi") else None),
                                  "locator": None, "verification": "literature_lead_not_reverified", "context": "wild" if typ.startswith("wild") else "captive",
                                  "plant_part": None, "finding": None}))
    return items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gbif-dir", type=Path, required=True)
    ap.add_argument("--max", type=int, required=True)
    ap.add_argument("--batch-label", default=None)
    a = ap.parse_args()
    species = jsonl(a.gbif_dir / "species.jsonl")
    vern = jsonl(a.gbif_dir / "vernacular.jsonl")
    existing_match = json.loads((a.gbif_dir / "existing_match.json").read_text(encoding="utf-8"))

    plants = load("data/plants.json")
    existing_names = {bare(p["scientific"]).casefold() for p in plants if bare(p["scientific"])}
    for p in plants:
        existing_names.update(t.casefold() for t in re.findall(r"\b([A-Z][a-z]+ [a-z][a-z-]+)\b", p.get("taxonomy_note") or ""))
    existing_keys = set()
    for m in existing_match.values():
        if m.get("matchType") == "EXACT":
            existing_keys.update(str(m[k]) for k in ("usageKey", "acceptedUsageKey", "speciesKey") if m.get(k))

    manifest = load("data/taxonomy-shards/index.json")
    cands = [(r["scientific_name"], r["taxon_id"].split(":")[1], "taxonomy_candidates_v1")
             for s in manifest["shards"] for r in load("data/taxonomy-shards/" + s["file"])["records"]]
    cands += [(r["scientific_name"], r["taxon_id"].split(":")[1], "diverse_taxonomy_candidates")
              for r in load("data/diverse_taxonomy_candidates.json")["records"]]

    # Evidence names resolved by exact, accepted GBIF match; ambiguous or synonym names are not linked.
    ev = evidence_sources()
    match = gbif_match({n for n, _ in ev if re.fullmatch(r"[A-Z][a-z]+ [a-z][a-z-]+", n)}, a.gbif_dir / "evidence_match.json")
    ev_by_key, ev_unlinked = {}, Counter()
    for n, item in ev:
        m = match.get(n) or {}
        if n in P1_HELD_NAMES:
            ev_unlinked["p1_identity_hold"] += 1; continue
        if m.get("matchType") != "EXACT" or m.get("status") != "ACCEPTED" or m.get("rank") != "SPECIES" or m.get("canonicalName") != n:
            ev_unlinked["no_exact_accepted_gbif_species"] += 1; continue
        item = dict(item, reported_name=n)
        lst = ev_by_key.setdefault(str(m["usageKey"]), [])
        if item not in lst:
            lst.append(item)
    # Species named in feeding sources come first, so every batch carries the entries that have evidence.
    by_key = {str(m["usageKey"]): n for n, m in match.items() if m.get("usageKey")}
    cands = [(by_key[k], k, "feeding_source_name") for k in sorted(ev_by_key)] + [c for c in cands if c[1] not in ev_by_key]
    prev = {}
    if (OUT / "index.json").exists():
        for s in load("data/plant-catalog/index.json")["shards"]:
            for r in load("data/plant-catalog/" + s["file"])["records"]:
                prev[r["id"]] = r
    records, rejected, seen_names, seen_keys = [], Counter(), set(), set()
    pending = load("data/feeding_pending_site_v1.json")
    for name, key, origin in cands:
        if len(records) >= a.max:
            break
        g = species.get(key)
        if g is None:
            rejected["gbif_not_fetched_yet"] += 1
            break  # keep batches in candidate order
        if "_http" in g:
            rejected["gbif_lookup_failed"] += 1; continue
        if g.get("kingdom") != "Plantae":
            rejected["not_plantae"] += 1; continue
        if g.get("rank") != "SPECIES":
            rejected["not_species_rank"] += 1; continue
        if g.get("taxonomicStatus") != "ACCEPTED":
            rejected["not_accepted_" + str(g.get("taxonomicStatus")).lower()] += 1; continue
        if g.get("canonicalName") != name:
            rejected["name_differs_from_gbif"] += 1; continue
        if name.casefold() in existing_names or key in existing_keys:
            rejected["already_in_reviewed_182"] += 1; continue
        if name.casefold() in seen_names or key in seen_keys:
            rejected["duplicate"] += 1; continue
        seen_names.add(name.casefold()); seen_keys.add(key)
        names = (vern.get(key) or {}).get("names") or []
        def pick(lang):
            out = []
            for x in names:
                v = " ".join(str(x.get("n") or "").split())
                if x.get("l") == lang and v and v.casefold() not in {o["name"].casefold() for o in out}:
                    out.append({"name": v[:1].upper() + v[1:] if lang == "eng" else v, "source": x.get("s") or "GBIF"})
            return out[:4]
        evidence = ev_by_key.get(key, [])
        tid = "gbif:" + key
        records.append({
            "id": tid, "scientific": name, "authorship": g.get("authorship") or None,
            "family": g.get("family"), "order": g.get("order"), "genus": g.get("genus"),
            "common_names": {"en": pick("eng"), "ko": pick("kor")},
            "taxonomy": {"source": "GBIF Backbone Taxonomy", "taxon_key": int(key), "url": "https://www.gbif.org/species/" + key,
                         "rank": "SPECIES", "status": "ACCEPTED", "kingdom": "Plantae", "checked": CHECKED, "candidate_list": origin},
            "feeding_safety_status": "unassessed", "safety_grade": None,
            "feeding_evidence_status": "linked" if evidence else "none_found",
            "feeding_evidence": evidence,
            "feeding_pending": tid in pending["site_feeding_pending"],
            "image": None,
            "batch": prev.get(tid, {}).get("batch") or a.batch_label,
        })
    # Records from earlier batches are never dropped silently.
    missing = sorted(set(prev) - {r["id"] for r in records})
    if missing:
        raise SystemExit(f"{len(missing)} earlier catalog entries would be dropped, e.g. {missing[:5]}")

    OUT.mkdir(parents=True, exist_ok=True)
    shards = [[] for _ in range(SHARDS)]
    for r in records:
        shards[r["taxonomy"]["taxon_key"] % SHARDS].append(r)
    meta = []
    for i, rows in enumerate(shards):
        rows.sort(key=lambda r: r["scientific"])
        raw = json.dumps({"schema_version": "1.0", "records": rows}, ensure_ascii=False, separators=(",", ":")) + "\n"
        f = OUT / f"taxa-{i:02d}.json"
        f.write_text(raw, encoding="utf-8")
        meta.append({"file": f.name, "count": len(rows), "sha256": hashlib.sha256(raw.encode()).hexdigest()})
    ordered = sorted(records, key=lambda r: r["scientific"])
    # Compact search index: [id, scientific, family, English name, Korean name, evidence flag, feeding_pending flag]
    rows = [[r["id"], r["scientific"], r["family"] or "", (r["common_names"]["en"] or [{"name": ""}])[0]["name"],
             (r["common_names"]["ko"] or [{"name": ""}])[0]["name"], 1 if r["feeding_evidence"] else 0, 1 if r["feeding_pending"] else 0]
            for r in ordered]
    (OUT / "search.json").write_text(json.dumps({"schema_version": "1.0", "fields": ["id", "scientific", "family", "en", "ko", "evidence", "feeding_pending"],
                                                 "rows": rows}, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    counts = {
        "entries": len(records),
        "with_feeding_evidence": sum(1 for r in records if r["feeding_evidence"]),
        "feeding_safety_unassessed": sum(1 for r in records if r["feeding_safety_status"] == "unassessed"),
        "with_safety_grade": sum(1 for r in records if r["safety_grade"]),
        "with_english_name": sum(1 for r in records if r["common_names"]["en"]),
        "with_korean_name": sum(1 for r in records if r["common_names"]["ko"]),
        "evidence_by_type": dict(Counter(e["type"] for r in records for e in r["feeding_evidence"])),
        "evidence_by_verification": dict(Counter(e["verification"] for r in records for e in r["feeding_evidence"])),
    }
    index = {"schema_version": "1.0", "generated": CHECKED, "scope": "Plant taxa confirmed in the GBIF Backbone Taxonomy. A taxon "
             "being valid is not feeding evidence; no entry has a feeding grade (feeding_safety_status unassessed = 급여 안전성 미확정).",
             "shard_rule": f"taxon_key % {SHARDS}", "count": len(records), "counts": counts,
             "rejected_in_candidate_order": dict(rejected), "evidence_names_not_linked": dict(ev_unlinked), "shards": meta}
    # GBIF matches of the reviewed plants, kept so QA can recheck the overlap offline.
    (OUT / "reviewed_gbif_match.json").write_text(json.dumps(dict(sorted(existing_match.items())), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    base = "https://jinwooson1988.github.io/tortoise-food-db-korea/taxon/?id="
    urls = []
    for r in ordered:
        u = base + urllib.parse.quote(r["id"], safe="")
        urls.append('<url><loc>%s</loc><xhtml:link rel="alternate" hreflang="ko" href="%s"/>'
                    '<xhtml:link rel="alternate" hreflang="en" href="%s&amp;lang=en"/></url>\n' % (u, u, u))
    (ROOT / "sitemap-taxa.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
                                         'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n' + "".join(urls) + "</urlset>\n", encoding="utf-8")
    (OUT / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    log = load("data/plant_catalog_batches_v1.json") if LOG.exists() else {"schema_version": "1.0", "batches": []}
    if a.batch_label and not any(b["label"] == a.batch_label for b in log["batches"]):
        before = log["batches"][-1]["entries_total"] if log["batches"] else 0
        log["batches"].append({"label": a.batch_label, "entries_total": len(records), "added": len(records) - before,
                               "with_feeding_evidence_total": counts["with_feeding_evidence"], "rejected_so_far": dict(rejected)})
        LOG.write_text(json.dumps(log, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"count": len(records), "counts": counts, "rejected": dict(rejected), "evidence_unlinked": dict(ev_unlinked)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
