#!/usr/bin/env python3
"""Parallel evidence triage for all taxonomy candidates. Offline, deterministic, no invented feeding claims.

Run: python scripts/parallel_feeding_evidence_triage.py --workers 20
Outputs local ignored/untracked review batches; inspect before committing.
"""
import argparse,concurrent.futures,json,re
from collections import defaultdict,Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_text(encoding="utf-8"))
def norm(s):
    return " ".join(re.sub(r"\\s+"," ",str(s or "").strip()).split()).casefold()
def exact_binomial(s):
    words=norm(s).split()
    return " ".join(words[:2]) if len(words)>=2 else ""
def candidate_shard(job):
    folder,file=job
    data=load(folder+"/"+file)
    return data.get("records",[])
def classify(e,scientific):
    # A taxonomy mention, composition study or genus-level reference is never proof of feeding.
    source=str(e.get("source_id") or e.get("source_url") or "")
    plant=str(e.get("plant_taxon_reported") or e.get("scientific_name") or "")
    animal=str(e.get("tortoise_taxon") or e.get("tortoise_taxon_reported") or "")
    typ=str(e.get("type") or e.get("source_type") or "")
    direct=str(e.get("directness") or "")
    excluded=any(x in typ.lower() for x in ("taxonomy","composition","nutrient"))
    exact=norm(plant)==norm(scientific) or exact_binomial(plant)==exact_binomial(scientific) and not any(x in plant.lower() for x in ("spp.","sp.","group","complex"))
    direct_feeding=direct in ("direct_feeding","observed_consumption","wild_feeding") or typ=="wild_feeding"
    animal_known=bool(animal and animal.lower() not in ("not_applicable","plant composition","unknown",""))
    return {"source_url":source,"source_type":typ,"plant_taxon_reported":plant,
      "tortoise_taxon_reported":animal,"taxon_match":"binomial_candidate" if exact else "requires_taxonomic_review",
      "evidence_class":"direct_feeding_lead_requires_original_review" if exact and direct_feeding and animal_known and not excluded and source.startswith(("http://","https://")) else "context_only_not_feeding_proof",
      "plant_part_reported":e.get("plant_part"),"directness":direct}
def main():
    p=argparse.ArgumentParser();p.add_argument("--workers",type=int,default=20);p.add_argument("--batch-size",type=int,default=500)
    p.add_argument("--output",default="data/feeding-triage")
    args=p.parse_args()
    if not 1<=args.workers<=32 or args.batch_size<1:p.error("invalid workers/batch-size")
    jobs=[]
    for folder in ("data/taxonomy-shards","data/evidence-first-queue"):
        idx=load(folder+"/index.json")
        jobs.extend((folder,s["file"]) for s in idx["shards"])
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        pieces=list(pool.map(candidate_shard,jobs))
    candidates=[r for chunk,job in zip(pieces,jobs) if job[0]=="data/taxonomy-shards" for r in chunk]
    queue=[r for chunk,job in zip(pieces,jobs) if job[0]=="data/evidence-first-queue" for r in chunk]
    diverse=load("data/diverse_taxonomy_candidates.json")["records"]
    linked=load("data/plant_feeding_evidence_links.json")["records"]
    evidence=defaultdict(list)
    for r in linked:
        for e in r.get("evidence",[]):evidence[exact_binomial(r.get("scientific_name"))].append(classify(e,r.get("scientific_name")))
    for r in queue:
        for e in r.get("mentions",[]):evidence[exact_binomial(r.get("scientific_name"))].append(classify(e,r.get("scientific_name")))
    output=ROOT/args.output;output.mkdir(parents=True,exist_ok=True)
    stats=Counter();batch=[];manifest=[]
    for r in candidates+diverse:
        name=r.get("scientific_name","")
        leads=evidence.get(exact_binomial(name),[])
        seen=set();unique=[]
        for lead in leads:
            key=(lead["source_url"],lead["plant_taxon_reported"],lead["evidence_class"])
            if key not in seen:seen.add(key);unique.append(lead)
        priority="source_review" if unique else "source_discovery"
        stats[priority]+=1
        if any(x["evidence_class"]=="direct_feeding_lead_requires_original_review" for x in unique):stats["direct_leads_not_yet_verified"]+=1
        batch.append({"scientific_name":name,"taxon_id":r.get("taxon_id"),"family":r.get("family"),
          "review_status":priority,"feeding_record_status":"not_verified",
          "feeding_safety_status":"not_assessed","safety_grade":None,
          "candidate_sources":unique,
          "feeding_details":{"tortoise_species":None,"plant_part":None,"mixed_with":None,
            "feeding_frequency":None,"feeding_amount":None,"presentation":None,
            "cutting_method":None,"original_source_locator":None},
          "warning":"Source links are leads, not confirmed feeding records or feeding recommendations."})
        if len(batch)>=args.batch_size:
            filename="batch-%03d.json"%(len(manifest)+1)
            (output/filename).write_text(json.dumps({"records":batch},ensure_ascii=False,separators=(",",":"))+"\\n",encoding="utf-8")
            manifest.append({"file":filename,"count":len(batch)});batch=[]
    if batch:
        filename="batch-%03d.json"%(len(manifest)+1)
        (output/filename).write_text(json.dumps({"records":batch},ensure_ascii=False,separators=(",",":"))+"\\n",encoding="utf-8")
        manifest.append({"file":filename,"count":len(batch)})
    summary={"total_input_records":len(candidates)+len(diverse),"reviewed_reference_records":len(linked),
      "review_queue_records":len(queue),"counts":dict(stats),"shards":manifest,
      "note":"No new feeding_pending status or A/B/C/D grade assigned. Original-source review required."}
    (output/"index.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in summary.items() if k!="shards"},ensure_ascii=False))
if __name__=="__main__":main()
