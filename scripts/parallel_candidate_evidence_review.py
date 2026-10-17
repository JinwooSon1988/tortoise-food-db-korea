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
    m=re.match(r"^([A-Z][a-z-]+)\\s+([a-z][a-z-]+)(?=\\s|$)",str(s or "").strip())
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
    if totals["candidates"]!=9995+len(rows):raise SystemExit("candidate count failed; do not publish")
    audit={"schema_version":"1.0","scope":"review-only; NOT safe-to-feed approval",
        "input_legacy":9995,"input_diverse":len(rows),"workers":args.workers,
        "shards":reports,"totals":dict(totals),"safety_grades_assigned":0}
    (out/"index.json").write_text(json.dumps(audit,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(audit["totals"],ensure_ascii=False))
if __name__=="__main__":main()
