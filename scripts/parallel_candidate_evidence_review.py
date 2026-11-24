#!/usr/bin/env python3
"""Validate 22k taxonomy candidates and join existing evidence in parallel.

No network calls; no grade promotion. Outputs review-only evidence shards.
Run: python scripts/parallel_candidate_evidence_review.py --workers 12
"""
import argparse,concurrent.futures,hashlib,json,re
from collections import Counter,defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads(p.read_text(encoding="utf-8"))
def norm(s):
    m=re.match(r"^([A-Z][a-z-]+)\s+([a-z][a-z-]+)(?=\s|$)",str(s or "").strip())
    return " ".join(m.groups()).casefold() if m else None
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--workers",type=int,default=12)
    args=ap.parse_args()
    if not 1<=args.workers<=20:ap.error("workers must be 1..20")
    data=ROOT/"data"; out=data/"evidence-review-shards";out.mkdir(exist_ok=True)
    manifest=load(data/"taxonomy-shards/index.json")
    diverse=load(data/"diverse_taxonomy_candidates.json")
    if manifest["count"]!=9995 or diverse["record_count"]!=len(diverse["records"]):raise SystemExit("input count mismatch")
    plants=load(data/"plants.json")
    links=load(data/"plant_feeding_evidence_links.json")
    reviewed=defaultdict(set)
    for p in plants:
        key=norm(p.get("scientific"))
        if key:reviewed[key].add(p["id"])
    evidence=defaultdict(list)
    for entry in links["records"]:
        for e in entry["evidence"]:
            evidence[entry["plant_id"]].append(e)
    quarantine={x.get("id") for x in links.get("quarantined_wild_records",[])}
    def eligible(e,key):
        # Strict feeding observation only, never inferred from genus-level data.
        return (e.get("type")=="wild_feeding" and e.get("evidence_id") not in quarantine
                and norm(e.get("plant_taxon_reported"))==key and bool(e.get("source_id"))
                and bool(e.get("tortoise_taxon")) and e.get("directness") in ("exact_species","direct"))
    def process(job):
        label,records=job
        seen=set();result=[];stats=Counter()
        for r in records:
            name=r.get("scientific_name");key=norm(name)
            if not key or key in seen:
                stats["invalid_or_duplicate_within_shard"]+=1;continue
            seen.add(key)
            ids=sorted(reviewed.get(key,[]))
            refs=[e for pid in ids for e in evidence.get(pid,[])]
            direct=[e for e in refs if eligible(e,key)]
            context=[e for e in refs if e.get("source_id")]
            practice=[]
            for e in direct:
                item={"source_url":e["source_id"],"tortoise_taxon":e["tortoise_taxon"]}
                for field in ("plant_part","mixed_with","feed_mixture","feeding_frequency","feeding_quantity","feeding_amount","presentation","preparation","cutting_method"):
                    if e.get(field):item[field]=e[field]
                practice.append(item)
            result.append({"taxon_id":r.get("taxon_id"),"scientific_name":name,
                "family":r.get("family"),"identity_status":"taxonomy_candidate",
                "feeding_record_status":"record_under_review" if direct else "not_verified",
                "feeding_record_evidence":practice,
                "reference_sources":[{"type":e.get("type"),"url":e.get("source_id"),"directness":e.get("directness")} for e in context],
                "safety_grade":None,"feeding_safety_status":"not_assessed"})
            stats["candidates"]+=1
            stats["with_any_reference"]+=bool(context)
            stats["with_direct_wild_record"]+=bool(direct)
            stats["matched_reviewed_identity"]+=bool(ids)
        raw=json.dumps({"schema_version":"1.0","count":len(result),"records":result},ensure_ascii=False,separators=(",",":"))+"\n"
        filename=label+".json";(out/filename).write_text(raw,encoding="utf-8")
        return {"file":filename,"count":len(result),"sha256":hashlib.sha256(raw.encode()).hexdigest(),"stats":dict(stats)}
    jobs=[]
    for i,sh in enumerate(manifest["shards"]):
        p=load(data/"taxonomy-shards"/sh["file"])
        if len(p["records"])!=sh["count"]:raise SystemExit("shard count mismatch "+sh["file"])
        jobs.append((f"legacy-{i+1:02d}",p["records"]))
    rows=diverse["records"]
    for i in range(0,len(rows),500):jobs.append((f"diverse-{i//500+1:02d}",rows[i:i+500]))
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        reports=list(pool.map(process,jobs))
    totals=Counter()
    for r in reports:totals.update(r["stats"])
    # A zero-match run must be visibly diagnosed, not mistaken for no published evidence.
    candidate_names={norm(rec.get("scientific_name")) for _,records in jobs for rec in records}
    candidate_names.discard(None)
    reviewed_names=set(reviewed)
    overlap=candidate_names & reviewed_names
    diagnostics={"candidate_unique_binomials":len(candidate_names),
        "reviewed_unique_binomials":len(reviewed_names),
        "candidate_reviewed_overlap":len(overlap),
        "evidence_linked_public_plant_ids":len(evidence),
        "overlap_with_linked_evidence":sum(any(pid in evidence for pid in reviewed[name]) for name in overlap),
        "explanation":"Review candidate taxonomy and public plant catalogs may be disjoint; zero matches must not be described as zero existing evidence."}
    if not overlap and evidence:
        diagnostics["join_warning"]="ZERO_CATALOG_OVERLAP: taxonomy candidates and published plants are disjoint; do not interpret as absence of feeding literature"
    # Audit the public evidence catalog independently: the 22k taxonomy-only
    # candidates have no exact overlap with the already published plant catalog.
    public_audit=[]
    for plant in plants:
        refs=evidence.get(plant["id"],[])
        public_audit.append({"plant_id":plant["id"],
            "scientific_name":plant.get("scientific"),
            "source_records":len(refs),
            "unique_source_urls":len({e.get("source_id") for e in refs if e.get("source_id")}),
            "missing_source_urls":sum(not e.get("source_id") for e in refs),
            "duplicate_evidence_ids":len([e.get("evidence_id") for e in refs if e.get("evidence_id")])-len({e.get("evidence_id") for e in refs if e.get("evidence_id")}),
            "source_types":dict(sorted(Counter(e.get("type","unspecified") for e in refs).items())),
            "directness_types":dict(sorted(Counter(e.get("directness","unspecified") for e in refs).items())),
            "tortoise_taxa_reported":sorted({str(e.get("tortoise_taxon")) for e in refs if e.get("tortoise_taxon")}),
            "wild_feeding_record_leads":sum(e.get("type")=="wild_feeding" for e in refs),
            "safety_grade":None,
            "feeding_safety_status":"not_assessed",
            "note":"Source coverage only; not an assessment of feeding safety."})
    public_audit.sort(key=lambda r:r["plant_id"])
    (out/"public-evidence-coverage.json").write_text(json.dumps({
        "schema_version":"1.0","scope":"public catalog source coverage, not safety verdict",
        "count":len(public_audit),"records":public_audit},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    diagnostics["public_catalog_rows_audited"]=len(public_audit)
    diagnostics["public_catalog_rows_with_sources"]=sum(r["source_records"]>0 for r in public_audit)
    diagnostics["public_catalog_total_source_records"]=sum(r["source_records"] for r in public_audit)
    diagnostics["public_catalog_unique_source_url_plant_pairs"]=sum(r["unique_source_urls"] for r in public_audit)
    diagnostics["public_catalog_missing_source_urls"]=sum(r["missing_source_urls"] for r in public_audit)
    diagnostics["public_catalog_duplicate_evidence_ids"]=sum(r["duplicate_evidence_ids"] for r in public_audit)
    all_source_urls=[e.get("source_id") for entry in links["records"] for e in entry["evidence"] if e.get("source_id")]
    source_plant_pairs={(entry["plant_id"],e.get("source_id")) for entry in links["records"] for e in entry["evidence"] if e.get("source_id")}
    diagnostics["global_unique_source_urls"]=len(set(all_source_urls))
    diagnostics["global_unique_source_plant_pairs"]=len(source_plant_pairs)
    url_plant_counts=Counter(url for _,url in source_plant_pairs)
    diagnostics["global_reused_source_urls_across_plants"]=sum(count>1 for count in url_plant_counts.values())
    diagnostics["global_duplicate_source_url_records"]=len(all_source_urls)-len(source_plant_pairs)
    # Actionable source-level review queue: retain attribution to every linked plant.
    url_to_plants=defaultdict(set)
    url_to_types=defaultdict(set)
    url_to_directness=defaultdict(set)
    url_to_tortoises=defaultdict(set)
    url_to_record_count=Counter()
    for entry in links["records"]:
        for e in entry["evidence"]:
            url=e.get("source_id")
            if not url:continue
            url_to_plants[url].add(entry["plant_id"])
            url_to_types[url].add(e.get("type","unspecified"))
            url_to_directness[url].add(e.get("directness","unspecified"))
            if e.get("tortoise_taxon"):url_to_tortoises[url].add(str(e["tortoise_taxon"]))
            url_to_record_count[url]+=1
    source_review=[{"source_url":url,"linked_plant_count":len(pids),
        "linked_plant_ids":sorted(pids),"source_types":sorted(url_to_types[url]),
        "directness_types":sorted(url_to_directness[url]),
        "tortoise_taxa_reported":sorted(url_to_tortoises[url]),
        "source_record_count":url_to_record_count[url],
        "review_status":"not_verified","feeding_safety_status":"not_assessed"}
        for url,pids in url_to_plants.items()]
    source_review.sort(key=lambda row:(-row["linked_plant_count"],row["source_url"]))
    (out/"global-source-review-queue.json").write_text(json.dumps({
        "schema_version":"1.0","scope":"source URL reuse triage; not evidence verification",
        "count":len(source_review),"records":source_review},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    diagnostics["global_source_review_queue_count"]=len(source_review)
    diagnostics["global_source_review_queue_record_count"]=sum(r["source_record_count"] for r in source_review)

    print(json.dumps({"join_diagnostics":diagnostics},ensure_ascii=False))
    if totals["candidates"]!=9995+len(rows):raise SystemExit("candidate count failed; do not publish")
    audit={"schema_version":"1.0","scope":"review-only; NOT safe-to-feed approval",
        "input_legacy":9995,"input_diverse":len(rows),"workers":args.workers,
        "shards":reports,"totals":dict(totals),"join_diagnostics":diagnostics,"safety_grades_assigned":0}
    (out/"index.json").write_text(json.dumps(audit,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(audit["totals"],ensure_ascii=False))
if __name__=="__main__":main()
