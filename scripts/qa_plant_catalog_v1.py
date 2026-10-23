#!/usr/bin/env python3
"""QA for the searchable plant catalog (data/plant-catalog/) and its pages.

Checks, offline: shard integrity and the shard rule; one entry per GBIF key and per name; required fields;
taxonomy recorded separately from feeding evidence; no feeding grade and status unassessed on every entry;
evidence typed, sourced, tied to a study and never from a P1-held claim (name and source); a link under another name only through a recorded
GBIF synonym or spelling variant; a research status on every entry that agrees with its evidence; corpus batch records
typed and sourced, and their held names never linked; no overlap with the reviewed plants (by name without
authors and by the stored GBIF keys); the reviewed plants and their grades unchanged; feeding_pending ids still
listed; the search index and taxon sitemap match the shards and list exactly the published detail pages; Korean names are in Hangul; the catalog page, detail page and both home
searches load the catalog; data sizes stay small enough for the static site.
"""
import hashlib, json, re, sys, urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import public_verdict as pv  # noqa: E402
from build_bulk_taxon_catalog import bare  # noqa: E402

CAT = ROOT / "data/plant-catalog"
TYPES = {"wild_feeding_observation", "captive_feeding_record", "husbandry_recommendation", "nutrition", "toxicity", "wild_diet_not_detected",
         "offered_not_eaten", "community_report", "video_observation"}
VERIFICATION = {"full_text_verified", "full_text_named_not_extracted", "literature_lead_not_reverified", "review_full_text_verified",
                "community_report_unverified", "guideline_full_text_verified", "video_observation_unverified", "abstract_checked",
                "full_text_auto_extracted", "reviewed_source_record"}
COMMUNITY = {"community_report_unverified", "video_observation_unverified"}
CHECKED = {"full_text_verified", "full_text_named_not_extracted", "review_full_text_verified", "guideline_full_text_verified",
           "reviewed_source_record"}
RESEARCH = {"evidence_checked_in_full_text", "evidence_auto_extracted", "evidence_leads_only", "community_reports_only", "reviewed_not_feeding_evidence", "no_record_found"}
NUTRITION_BASIS = {"dry_matter", "as_fed", "unstated"}
NAME_BASIS = {"gbif_synonym", "orthographic_variant"}
from build_plant_catalog_v1 import P1_HELD_CLAIMS, HANGUL, source_id  # noqa: E402
errors = []
load = lambda p: json.loads(Path(p).read_text(encoding="utf-8"))

index = load(CAT / "index.json")
shards = int(re.fullmatch(r"taxon_key % (\d+)", index["shard_rule"]).group(1))
records = []
for i, s in enumerate(index["shards"]):
    raw = (CAT / s["file"]).read_text(encoding="utf-8")
    if hashlib.sha256(raw.encode()).hexdigest() != s["sha256"]:
        errors.append(f"{s['file']}: sha256 mismatch")
    rows = json.loads(raw)["records"]
    if len(rows) != s["count"] or s["file"] != f"taxa-{i:02d}.json":
        errors.append(f"{s['file']}: count or name mismatch")
    for r in rows:
        if r["taxonomy"]["taxon_key"] % shards != i:
            errors.append(f"{r['id']}: in the wrong shard")
    records += rows
if len(records) != index["count"]:
    errors.append(f"index count {index['count']} != {len(records)} records")

ids, names = set(), set()
for r in records:
    key = r["taxonomy"]["taxon_key"]
    if r["id"] != f"gbif:{key}" or r["id"] in ids:
        errors.append(f"{r['id']}: bad or duplicate id")
    if not re.fullmatch(r"[A-Z][a-z-]+ [a-z][a-z-]+", r["scientific"]) or r["scientific"].casefold() in names:
        errors.append(f"{r['id']}: bad or duplicate scientific name {r['scientific']}")
    ids.add(r["id"]); names.add(r["scientific"].casefold())
    t = r["taxonomy"]
    if (t["source"], t["rank"], t["status"], t["kingdom"]) != ("GBIF Backbone Taxonomy", "SPECIES", "ACCEPTED", "Plantae") \
            or t["url"] != f"https://www.gbif.org/species/{key}" or not t.get("checked"):
        errors.append(f"{r['id']}: taxonomy source incomplete")
    if not r.get("family"):
        errors.append(f"{r['id']}: family missing")
    if r["feeding_safety_status"] != "unassessed" or r["safety_grade"] is not None:
        errors.append(f"{r['id']}: a catalog entry carries a feeding grade or a status other than unassessed")
    if r["image"] is not None:
        errors.append(f"{r['id']}: image set without the verified image registry")
    if r["feeding_evidence_status"] != ("linked" if r["feeding_evidence"] else "none_found"):
        errors.append(f"{r['id']}: feeding_evidence_status does not match the evidence")
    for e in r["feeding_evidence"]:
        if e["type"] not in TYPES or e["verification"] not in VERIFICATION or not e.get("source") or not e.get("tortoise"):
            errors.append(f"{r['id']}: evidence item missing type, verification, source or tortoise")
        if (e["reported_name"], source_id(e.get("url"))) in P1_HELD_CLAIMS:
            errors.append(f"{r['id']}: evidence from a P1-held claim {e['reported_name']} ({e.get('url')})")
        nr = e.get("name_resolution")
        if e["reported_name"] != r["scientific"] and not (nr and nr.get("basis") in NAME_BASIS and nr.get("reported") == e["reported_name"]
                                                        and nr.get("accepted") == r["scientific"]):
            errors.append(f"{r['id']}: evidence reported as {e['reported_name']} linked to {r['scientific']}")
        if nr and e["reported_name"] == r["scientific"]:
            errors.append(f"{r['id']}: name_resolution on an exact-name link")
        if re.fullmatch(r"[a-z0-9_]+", e["source"]):
            errors.append(f"{r['id']}: internal id {e['source']} shown as the source citation")
        if not e.get("study"):
            errors.append(f"{r['id']}: evidence item without a study id")
        if e["type"] == "nutrition" and not ((e.get("nutrition") or {}).get("basis") in NUTRITION_BASIS and e["nutrition"].get("part")):
            errors.append(f"{r['id']}: nutrition record without plant part and dry-matter/as-fed basis")
        if e["type"] == "toxicity" and not ((e.get("toxicity") or {}).get("test_animal") and e["toxicity"].get("conditions")):
            errors.append(f"{r['id']}: toxicity record without test animal and conditions")
    research = r.get("research") or {}
    expect_status = ("evidence_checked_in_full_text" if any(e["verification"] in CHECKED for e in r["feeding_evidence"])
                     else "evidence_auto_extracted" if any(e["verification"] == "full_text_auto_extracted" for e in r["feeding_evidence"])
                     else "evidence_leads_only" if any(e["verification"] not in COMMUNITY for e in r["feeding_evidence"])
                     else "community_reports_only" if r["feeding_evidence"] else None)
    if research.get("status") not in RESEARCH or not research.get("corpus") or \
            (expect_status and research["status"] != expect_status) or (not expect_status and research["status"] in ("evidence_checked_in_full_text", "evidence_auto_extracted", "evidence_leads_only", "community_reports_only")):
        errors.append(f"{r['id']}: research status missing or inconsistent with the evidence")
    for lang in ("en", "ko"):
        for n in r["common_names"][lang]:
            if not n.get("name") or not n.get("source"):
                errors.append(f"{r['id']}: common name without source")
            if lang == "ko" and not HANGUL.search(n.get("name") or ""):
                errors.append(f"{r['id']}: Korean name not in Hangul: {n.get('name')}")

# Corpus evidence batches: typed, sourced records; held names never reach the catalog; the corpus searched is described.
linked_reported = {e["reported_name"] for r in records for e in r["feeding_evidence"]}
from build_plant_catalog_v1 import batch_files as _batch_files  # noqa: E402
batch_files = _batch_files()  # numbered corpus batches and the reviewer-approved batch; not the site index
for f in batch_files:
    b = load(f)
    src = {s["source_key"]: s for s in b["sources"]}
    for x in b["records"]:
        s = src.get(x["source_key"])
        if not s or not s.get("citation") or not s.get("url") or not s.get("study_id") or x["type"] not in TYPES or x["verification"] not in VERIFICATION:
            errors.append(f"{f.name}: record {x['reported_name']} lacks a typed, sourced study")
        if not re.fullmatch(r"[A-Z][a-z-]+ [a-z][a-z-]+", x["reported_name"]):
            errors.append(f"{f.name}: record name {x['reported_name']} is not a binomial")
        if (x["verification"] in COMMUNITY or x["type"] in ("community_report", "video_observation")) and x.get("identification") != "binomial_in_source":
            errors.append(f"{f.name}: community or video record {x['reported_name']} linked without a scientific name printed in the source")
        if (x["verification"] in COMMUNITY) != (x["type"] in ("community_report", "video_observation")):
            errors.append(f"{f.name}: record {x['reported_name']} mixes a community/video type with a research verification level")
    for h in b.get("held_not_linked", []):
        # a name held as a name (identity doubt) must never be linked; a record held for its own reasons may share a name linked elsewhere
        if h.get("scope", "name") == "name" and h["reported_name"] in linked_reported:
            errors.append(f"{f.name}: held name {h['reported_name']} is linked in the catalog")
if batch_files and [c["id"] for c in index.get("research_corpus", [])] != [load(f)["corpus"]["id"] for f in batch_files]:
    errors.append("index.json research_corpus does not describe the evidence batches")

plants = load(ROOT / "data/plants.json")
reviewed_names = {bare(p["scientific"]).casefold() for p in plants if bare(p["scientific"])}
match = load(CAT / "reviewed_gbif_match.json")
reviewed_keys = {f"gbif:{m[k]}" for m in match.values() if m.get("matchType") == "EXACT"
                 for k in ("usageKey", "acceptedUsageKey", "speciesKey") if m.get(k)}
if names & reviewed_names or ids & reviewed_keys:
    errors.append(f"catalog repeats reviewed plants: {sorted(names & reviewed_names)[:5]} {sorted(ids & reviewed_keys)[:5]}")
missing_match = {p["scientific"] for p in plants} - set(match)
if missing_match:
    errors.append(f"reviewed plants without a stored GBIF match: {sorted(missing_match)[:5]}")

baseline = load(CAT / "reviewed_grade_baseline.json")
grade = {pid: pv.display(pv.representative(rows))["grade"] for pid, rows in pv.by_plant(pv.load_assessments()).items()}
now = {p["id"]: grade.get(p["id"]) for p in plants}
if len(plants) != baseline["plants"] or now != baseline["grades"]:
    changed = sorted(k for k in set(now) | set(baseline["grades"]) if now.get(k) != baseline["grades"].get(k))
    errors.append(f"reviewed plants or grades changed: {changed[:10]}")

pending = load(ROOT / "data/feeding_pending_site_v1.json")["site_feeding_pending"]
lost = [p for p in pending if p not in ids and p not in now]
if lost:
    errors.append(f"feeding_pending entries no longer listed: {lost}")

search = load(CAT / "search.json")
expect = [[r["id"], r["scientific"], r["family"] or "", (r["common_names"]["en"] or [{"name": ""}])[0]["name"],
           (r["common_names"]["ko"] or [{"name": ""}])[0]["name"], 1 if r["feeding_evidence"] else 0, 1 if r["feeding_pending"] else 0]
          for r in sorted(records, key=lambda r: r["scientific"])]
if search["rows"] != expect:
    errors.append("search.json does not match the shards")
sitemap = (ROOT / "sitemap-taxa.xml").read_text(encoding="utf-8")
locs = re.findall(r"<loc>(.*?)</loc>", sitemap)
# The sitemap lists exactly the published detail pages: entries with linked evidence or a Batch 002 record (taxon/index.html hides the rest).
b2_names = set(load(ROOT / "data/catalog-evidence/batch-002-site-index.json")["by_scientific_name"])
published = [r for r in records if r["feeding_evidence"] or r["scientific"].strip().lower() in b2_names]
loc_ids = {urllib.parse.unquote(u.split("?id=", 1)[1]) for u in locs if "?id=" in u}
if len(locs) != len(published) or len(set(locs)) != len(locs) or len(locs) > 50000:
    errors.append(f"sitemap-taxa.xml has {len(locs)} URLs for {len(published)} published entries")
# The catalog list (search.json evidence flag), the detail page and the sitemap publish the same entries.
listed = {row[0] for row in search["rows"] if row[5]}
if listed != {r["id"] for r in records if r["feeding_evidence"]}:
    errors.append(f"listed and published detail pages differ: {sorted(listed ^ {r['id'] for r in published})[:10]}")
if loc_ids != {r["id"] for r in published}:
    errors.append(f"sitemap-taxa.xml differs from the published entries: {sorted(loc_ids ^ {r['id'] for r in published})[:10]}")
if "sitemap-taxa.xml" not in (ROOT / "robots.txt").read_text(encoding="utf-8"):
    errors.append("robots.txt does not list sitemap-taxa.xml")

pages = {
    "all-plants/index.html": ["../data/plant-catalog/search.json", "../taxon/?id=", "급여 안전성 미확정", "Feeding safety not established",
                              "feedingRecordPending:feedingIds.has(t.taxon_id)"],
    "taxon/index.html": ["../data/plant-catalog/taxa-", "급여 안전성 미확정", "Feeding safety not established", "검증된 이미지 준비 중",
                         "Verified photo pending", "../language-toggle.js", "const SHARDS=%d;" % shards, "조사 현황", "Research status",
                         "자료 미확보", "No data found"] + sorted(TYPES | VERIFICATION),
    "taxonomy-home-search.js": ["data/plant-catalog/search.json", "taxon/?id=", "급여 안전성 미확정"],
    "index.html": ["taxonomy-home-search.js"],
    # the English homepage now redirects to the bilingual homepage, which loads the catalog search
    "en/index.html": ["../?lang=en"],
}
for page, needles in pages.items():
    text = (ROOT / page).read_text(encoding="utf-8")
    for n in needles:
        if n not in text:
            errors.append(f"{page}: missing {n}")
for f, limit in [(CAT / "search.json", 3_000_000)] + [(CAT / s["file"], 1_000_000) for s in index["shards"]]:
    if f.stat().st_size > limit:
        errors.append(f"{f.name}: {f.stat().st_size} bytes exceeds {limit}")

if errors:
    print("FAIL plant catalog:")
    for e in errors[:40]:
        print(" -", e)
    sys.exit(1)
print(f"PASS plant catalog: {len(records)} entries, {sum(1 for r in records if r['feeding_evidence'])} with feeding evidence, "
      f"0 grades; {len(plants)} reviewed plants and grades unchanged; search index, shards and sitemap agree")
