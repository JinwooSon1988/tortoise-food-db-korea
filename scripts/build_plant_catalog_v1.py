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
repository sources (including data/catalog-evidence/batch-*.json), by type, and only where the reported name is an exact
accepted GBIF species, a GBIF synonym of an accepted species, or an orthographic variant (doubled i, gender ending); such
links keep the printed name and record name_resolution. Every entry records its research status for the searched corpus;
"no_record_found" is never a safety or toxicity finding.

--max caps the number of entries (batches are appended in candidate order; earlier entries are kept).
"""
import argparse, hashlib, json, re, sys, urllib.parse
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
P1_MANIFEST = "data/feeding_p1_blocked_claim_manifest_20261018.json"
HANGUL = re.compile(r"[가-힣]")


def source_id(value):
    """DOI or host+path of a source, so every spelling of the same source compares equal."""
    v = str(value or "").strip().lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "https://dx.doi.org/", "doi:"):
        if v.startswith(prefix):
            return "doi:" + v[len(prefix):]
    if v.startswith("10."):
        return "doi:" + v
    u = urllib.parse.urlsplit(v)
    # publisher pages that carry the DOI in the path (e.g. .../articles/10.3389/x.2023.1/full)
    d = re.search(r"/(10\.\d{4,9}/[^?#]+?)(?:/(?:full|abstract|pdf))?/?$", u.path) if u.scheme else None
    if d:
        return "doi:" + d.group(1)
    return u.netloc + u.path.rstrip("/") if u.scheme else v


def p1_held_claims():
    """(reported name, source) pairs held by the P1 manifest. The hold covers that source's claim only: the same
    plant reported by an independent source is linked as usual."""
    m = json.loads((ROOT / P1_MANIFEST).read_text(encoding="utf-8"))
    return {(c.get("plant_taxon_reported") or c.get("reported_taxon"), source_id(c["source"])) for c in m["blocked_claims"]}


P1_HELD_CLAIMS = p1_held_claims()
EVIDENCE_TYPES = ("wild_feeding_observation", "captive_feeding_record", "husbandry_recommendation", "nutrition", "toxicity")
BATCH_DIR = "data/catalog-evidence"


def evidence_first_priority(names, evidence_names):
    """Stable ordering: source-mentioned plants first; taxonomy-only candidates last.

    Names are compared after whitespace/case normalization only. This function
    never resolves synonyms or creates feeding evidence.
    """
    def key(name):
        return " ".join(str(name).casefold().split())
    evidence_keys = {key(n) for n in evidence_names}
    return sorted(names, key=lambda n: (key(n) not in evidence_keys, key(n)))


def batch_files():
    """Corpus batch files (batch-NNN-YYYYMMDD.json); other files in the folder, such as a site index, are not batches."""
    return [p for p in sorted((ROOT / BATCH_DIR).glob("batch-*.json")) if re.fullmatch(r"batch-\d{3}-\d{8}\.json", p.name)]


SYNONYM_STATUS = ("SYNONYM", "HOMOTYPIC_SYNONYM", "HETEROTYPIC_SYNONYM")
# Verification levels where the record was read in a full text (the rest are leads to recheck).
CHECKED_LEVELS = ("full_text_verified", "full_text_named_not_extracted", "review_full_text_verified", "guideline_full_text_verified")
# Keeper experience and uploader-described videos are shown as references only, apart from leads and checked records.
COMMUNITY_LEVELS = ("community_report_unverified", "video_observation_unverified")
# Found by the batch 004 extractor in an open full text and re-found verbatim; not read by a person.
AUTO_LEVELS = ("full_text_auto_extracted",)


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
    new = sorted(set(names) - set(cache))
    if new:
        from polite_http import PoliteClient  # robots.txt, GBIF request spacing, retries, provenance log
        client = PoliteClient(provenance=cache_path.parent / "gbif_requests.jsonl")
        for n in new:
            u = "https://api.gbif.org/v1/species/match?" + urllib.parse.urlencode({"name": n, "kingdom": "Plantae", "strict": "true"})
            d, _ = client.get_json(u, purpose="gbif name match")
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
                "verification": "full_text_verified", "plant_part": None, "context": "wild", "study": "elmouden_2006_central_morocco"}
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
            "finding": r["observed"] and {"ko": r["observed"]["ko"], "en": r["observed"]["en"]}, "study": r["source_key"]}))
    named = ext["species_in_full_text_not_in_catalog"]
    for key, names in named.items():
        if key in src and isinstance(names, list):
            s = src[key]
            for n in names:
                items.append((n, {"type": "wild_feeding_observation", "tortoise": s["tortoise_taxon"], "source": s["citation"],
                                  "url": s["url"], "locator": None, "verification": "full_text_named_not_extracted",
                                  "context": s["context"], "plant_part": None, "finding": None, "study": key}))
    # Open-access full texts, keeper database entries and corpus batches (records carry their own verification level).
    for f in ["data/catalog_feeding_evidence_fulltext_20261020.json"] + [str(p.relative_to(ROOT)) for p in sorted(batch_files())]:
        ft = load(f)
        src = {s["source_key"]: s for s in ft["sources"]}
        for r in ft["records"]:
            s = src[r["source_key"]]
            item = {"type": r["type"], "tortoise": r.get("tortoise") or s["tortoise_taxon"], "source": s["citation"], "url": s["url"],
                    "locator": r["locator"], "verification": r["verification"], "context": r.get("context") or s["context"],
                    "plant_part": r["plant_part"], "finding": r["finding"], "study": s.get("study_id") or r["source_key"]}
            if s.get("method"):
                item["method"] = s["method"]
            for k in ("source_class", "language"):
                if s.get(k):
                    item[k] = s[k]
            for k in ("nutrition", "toxicity", "identification", "outcome", "platform"):
                if r.get(k):
                    item[k] = r[k]
            items.append((r["reported_name"], item))
    for f in sorted((ROOT / "research/evidence_leads").glob("*.json")):
        for r in json.loads(f.read_text(encoding="utf-8"))["records"]:
            names = r.get("observed_plant_taxa") or r.get("plant_taxa") or []
            kind = r.get("evidence_directness") or ""
            typ = "captive_feeding_record" if "captive" in kind else "wild_feeding_observation"
            for n in names:
                items.append((n, {"type": typ, "tortoise": r.get("animal_taxon"), "source": r.get("source_title"),
                                  "url": r.get("url") or r.get("source_url") or ("https://doi.org/" + r["doi"] if r.get("doi") else None),
                                  "locator": None, "verification": "literature_lead_not_reverified", "context": "wild" if typ.startswith("wild") else "captive",
                                  "plant_part": None, "finding": None, "study": r.get("id") or r.get("source_id") or r.get("doi") or f.stem}))
    # Leads without a title get the citation of another record from the same source (same DOI or URL), else the DOI or
    # URL itself, so an internal lead id is never shown as a citation.
    cited = {}
    for _, it in items:
        if it["source"] and it.get("url"):
            cited.setdefault(source_id(it["url"]), it["source"])
    for _, it in items:
        if not it["source"]:
            sid = source_id(it.get("url"))
            it["source"] = cited.get(sid) or (("DOI " + sid[4:]) if sid.startswith("doi:") else it.get("url") or it["study"])
    return items


def orthographic_variant(a, b):
    """True when two binomials share the genus and their epithets differ only by a doubled final i or a Latin gender ending."""
    (ga, ea), (gb, eb) = a.split(" ", 1), b.split(" ", 1)
    if ga != gb or ea == eb:
        return False
    for group in (("ii", "i"), ("us", "a", "um"), ("is", "e")):
        for x in group:
            for y in group:
                if x != y and ea.endswith(x) and eb.endswith(y) and ea[:-len(x)] == eb[:-len(y)]:
                    return True
    return False


def resolve(n, m):
    """(catalog key, basis) for a reported name, or (None, None). basis None means an exact accepted species match."""
    if m.get("rank") != "SPECIES" or not m.get("usageKey"):
        return None, None
    if m.get("matchType") == "EXACT" and m.get("status") == "ACCEPTED" and m.get("canonicalName") == n:
        return str(m["usageKey"]), None
    if m.get("matchType") == "EXACT" and m.get("status") in SYNONYM_STATUS and m.get("canonicalName") == n and m.get("acceptedUsageKey"):
        return str(m["acceptedUsageKey"]), "gbif_synonym"
    if m.get("matchType") == "FUZZY" and m.get("status") == "ACCEPTED" and orthographic_variant(n, m.get("canonicalName") or ""):
        return str(m["usageKey"]), "orthographic_variant"
    return None, None


def research_status(evidence, rejected):
    if any(e["verification"] in CHECKED_LEVELS for e in evidence):
        return "evidence_checked_in_full_text"
    if any(e["verification"] in AUTO_LEVELS for e in evidence):
        return "evidence_auto_extracted"
    if any(e["verification"] not in COMMUNITY_LEVELS for e in evidence):
        return "evidence_leads_only"
    if evidence:
        return "community_reports_only"
    return "reviewed_not_feeding_evidence" if rejected else "no_record_found"


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
        # The species of a reviewed subspecies or variety (e.g. carrot top, Daucus carota subsp. sativus) is not listed again.
        sp = re.match(r"([A-Z][a-z]+ [a-z][a-z-]+) (?:subsp|var|f)\.", p["scientific"])
        if sp:
            existing_names.add(sp.group(1).casefold())
    existing_keys = set()
    for m in existing_match.values():
        if m.get("matchType") == "EXACT":
            existing_keys.update(str(m[k]) for k in ("usageKey", "acceptedUsageKey", "speciesKey") if m.get(k))

    manifest = load("data/taxonomy-shards/index.json")
    cands = [(r["scientific_name"], r["taxon_id"].split(":")[1], "taxonomy_candidates_v1")
             for s in manifest["shards"] for r in load("data/taxonomy-shards/" + s["file"])["records"]]
    cands += [(r["scientific_name"], r["taxon_id"].split(":")[1], "diverse_taxonomy_candidates")
              for r in load("data/diverse_taxonomy_candidates.json")["records"]]

    # Evidence names resolved by an exact accepted GBIF species match, a GBIF synonym of an accepted species, or an
    # orthographic variant (doubled i, gender ending); the name printed in the source is kept as reported_name.
    ev = evidence_sources()
    batches = [load(str(p.relative_to(ROOT))) for p in sorted(batch_files())]
    rejected_names = {n for b in batches for x in b.get("reviewed_not_feeding_evidence", []) for n in x["names"]}
    binomial = lambda n: re.fullmatch(r"[A-Z][a-z]+ [a-z][a-z-]+", n)
    match = gbif_match({n for n, _ in ev if binomial(n)} | {n for n in rejected_names if binomial(n)}, a.gbif_dir / "evidence_match.json")
    ev_by_key, ev_unlinked, resolved_by = {}, Counter(), Counter()
    for n, item in ev:
        if (n, source_id(item.get("url"))) in P1_HELD_CLAIMS:
            ev_unlinked["p1_identity_hold"] += 1; continue
        key, basis = resolve(n, match.get(n) or {})
        if key is None:
            ev_unlinked["no_exact_accepted_gbif_species"] += 1; continue
        item = dict(item, reported_name=n)
        if basis:
            item["name_resolution"] = {"basis": basis, "reported": n, "gbif_usage_key": (match[n] or {}).get("usageKey")}
            resolved_by[basis] += 1
        lst = ev_by_key.setdefault(key, [])
        if item not in lst:
            lst.append(item)
    corpus_id = batches[-1]["corpus"]["id"] if batches else None
    rejected_keys = {k for n in rejected_names for k, b in [resolve(n, match.get(n) or {})] if k and b is None}
    # Species named in feeding sources come first, so every batch carries the entries that have evidence.
    by_key = {str(m["usageKey"]): n for n, m in match.items() if m.get("usageKey")}
    for k in ev_by_key:
        if (species.get(k) or {}).get("canonicalName"):
            by_key[k] = species[k]["canonicalName"]  # accepted name for keys reached through a synonym or variant
        elif k not in by_key or any(e.get("name_resolution") for e in ev_by_key[k]):
            by_key[k] = "(GBIF record not fetched yet)"
    unfetched = sorted(k for k in ev_by_key if k not in species)
    if unfetched:
        (a.gbif_dir / "missing_keys.txt").write_text("\n".join(unfetched) + "\n", encoding="utf-8")
        raise SystemExit(f"{len(unfetched)} evidence keys have no GBIF species record yet; listed in {a.gbif_dir / 'missing_keys.txt'}")
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
                # Korean names must be written in Hangul; romanized entries (e.g. "gaeyanggwibi") are not shown as Korean.
                if lang == "kor" and not HANGUL.search(v):
                    continue
                if x.get("l") == lang and v and v.casefold() not in {o["name"].casefold() for o in out}:
                    out.append({"name": v[:1].upper() + v[1:] if lang == "eng" else v, "source": x.get("s") or "GBIF"})
            return out[:4]
        evidence = [dict(e, name_resolution=dict(e["name_resolution"], accepted=name)) if e.get("name_resolution") else e
                    for e in ev_by_key.get(key, [])]
        tid = "gbif:" + key
        records.append({
            "id": tid, "scientific": name, "authorship": g.get("authorship") or None,
            "family": g.get("family"), "order": g.get("order"), "genus": g.get("genus"),
            "common_names": {"en": pick("eng"), "ko": pick("kor")},
            "taxonomy": {"source": "GBIF Backbone Taxonomy", "taxon_key": int(key), "url": "https://www.gbif.org/species/" + key,
                         "rank": "SPECIES", "status": "ACCEPTED", "kingdom": "Plantae", "checked": CHECKED,
                         "candidate_list": prev.get(tid, {}).get("taxonomy", {}).get("candidate_list") or origin},
            "feeding_safety_status": "unassessed", "safety_grade": None,
            "feeding_evidence_status": "linked" if evidence else "none_found",
            "feeding_evidence": evidence,
            "research": {"status": research_status(evidence, key in rejected_keys), "corpus": corpus_id},
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
        "evidence_studies": len({e["study"] for r in records for e in r["feeding_evidence"]}),
        "evidence_linked_by_name_resolution": dict(Counter(e["name_resolution"]["basis"] for r in records for e in r["feeding_evidence"] if e.get("name_resolution"))),
        "research_status": dict(Counter(r["research"]["status"] for r in records)),
    }
    linked_keys = {r["taxonomy"]["taxon_key"] for r in records}
    ev_unlinked["species_not_in_catalog"] = sum(len(v) for k, v in ev_by_key.items() if int(k) not in linked_keys)
    index = {"schema_version": "1.0", "generated": CHECKED, "scope": "Plant taxa confirmed in the GBIF Backbone Taxonomy. A taxon "
             "being valid is not feeding evidence; no entry has a feeding grade (feeding_safety_status unassessed = 급여 안전성 미확정).",
             "shard_rule": f"taxon_key % {SHARDS}", "count": len(records), "counts": counts,
             "rejected_in_candidate_order": dict(rejected), "evidence_names_not_linked": dict(ev_unlinked),
             "research_corpus": [dict(b["corpus"], batch=b["batch"]) for b in batches],
             "research_status_meaning": {
                 "evidence_checked_in_full_text": "at least one feeding record read in a full text (original study, review or species account)",
                 "evidence_auto_extracted": "feeding records found automatically in an open full text and re-found verbatim; not yet read by a person",
                 "evidence_leads_only": "only literature leads not yet rechecked in the original",
                 "community_reports_only": "only keeper, community or video reports (a reference, not verified research)",
                 "reviewed_not_feeding_evidence": "named in a tortoise paper that was read, but not as food (e.g. habitat or plant availability)",
                 "no_record_found": "no feeding record found in the searched corpus; this is not a safety or toxicity finding"},
             "shards": meta}
    # GBIF matches of the reviewed plants, kept so QA can recheck the overlap offline.
    (OUT / "reviewed_gbif_match.json").write_text(json.dumps(dict(sorted(existing_match.items())), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    base = "https://jinwooson1988.github.io/tortoise-food-db-korea/taxon/?id="
    # Only entries whose detail page is published (linked feeding evidence, or a Batch 002 record matched by exact name);
    # taxonomy-only entries are not food profiles, so taxon/index.html hides them and they stay out of the sitemap.
    b2 = ROOT / BATCH_DIR / "batch-002-site-index.json"
    b2_names = set(json.loads(b2.read_text(encoding="utf-8"))["by_scientific_name"]) if b2.exists() else set()
    urls = []
    for r in ordered:
        if not r["feeding_evidence"] and r["scientific"].strip().lower() not in b2_names:
            continue
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
