#!/usr/bin/env python3
"""Expand botanical candidates across neglected plant families via GBIF.
Taxonomy only: NEVER assert feeding, toxicity or A-D safety from a GBIF record.
Usage: python scripts/expand_global_plant_families.py --workers 8 --per-family 350
Network required; outputs data/diverse_taxonomy_candidates.json and audit.
"""
import argparse,collections,concurrent.futures,hashlib,json,time,urllib.error,urllib.parse,urllib.request,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FAMILIES=("Asteraceae","Fabaceae","Brassicaceae","Plantaginaceae","Malvaceae","Rosaceae",
"Lamiaceae","Apiaceae","Amaranthaceae","Polygonaceae","Caryophyllaceae","Campanulaceae",
"Geraniaceae","Violaceae","Boraginaceae","Rubiaceae","Convolvulaceae","Onagraceae",
"Crassulaceae","Moraceae","Urticaceae","Caprifoliaceae","Cactaceae","Portulacaceae",
"Amaryllidaceae","Asparagaceae","Araceae","Euphorbiaceae","Solanaceae","Ranunculaceae",
"Apocynaceae","Oxalidaceae","Primulaceae","Aizoaceae","Talinaceae","Montiaceae",
"Poaceae","Cyperaceae","Juncaceae")
URL="https://api.gbif.org/v1"
def get(path,params=None):
    u=URL+path+("?"+urllib.parse.urlencode(params) if params else "")
    for attempt in range(5):
        try:
            req=urllib.request.Request(u,headers={"User-Agent":"Geobukbap-taxonomy-research/1.0","Accept":"application/json"})
            with urllib.request.urlopen(req,timeout=35) as r:return json.load(r)
        except (urllib.error.URLError,TimeoutError,ValueError) as exc:
            if attempt==4:raise RuntimeError(f"{u}: {exc}") from exc
            time.sleep(min(2**attempt,16))
def existing():
    out=set()
    shard=ROOT/"data/taxonomy-shards"
    if shard.exists():
        for p in shard.glob("taxa-??.json"):
            for row in json.loads(p.read_text(encoding="utf-8"))["records"]:
                out.add(row["scientific_name"].casefold())
    p=ROOT/"data/plants.json"
    if p.exists():
        for row in json.loads(p.read_text(encoding="utf-8")):
            name=" ".join(str(row.get("scientific","")).split()[:2])
            if name:out.add(name.casefold())
    return out
def family_records(family,limit):
    match=get("/species/match",{"name":family,"rank":"FAMILY","strict":"true"})
    if match.get("rank")!="FAMILY" or match.get("matchType")=="NONE" or str(match.get("scientificName","")).split()[0].casefold()!=family.casefold():
        raise ValueError(f"family match not verified: {family}: {match}")
    key=match["usageKey"]
    rows=[];offset=0;scanned=0
    # Offset pagination is bounded to avoid infinite/expensive crawling.
    while len(rows)<limit and offset<10000:
        data=get("/species/search",{"higherTaxonKey":key,"rank":"SPECIES","status":"ACCEPTED","limit":300,"offset":offset})
        batch=data.get("results",[])
        if not batch:break
        scanned+=len(batch);offset+=len(batch)
        for r in batch:
            if r.get("rank")!="SPECIES" or r.get("taxonomicStatus")!="ACCEPTED":continue
            if str(r.get("family","")).casefold()!=family.casefold():continue
            canonical=r.get("canonicalName","").strip()
            words=canonical.split()
            if len(words)!=2 or not words[0][:1].isupper() or not words[1][:1].islower():continue
            if not isinstance(r.get("key"),int):continue
            if r.get("kingdom")!="Plantae":continue
            rows.append({"scientific_name":canonical,"family":family,
                "source_taxon_url":f"https://www.gbif.org/species/{r['key']}",
                "taxon_id":f"gbif:{r['key']}","identity_status":"taxonomy_candidate",
                "feeding_evidence_status":"not_reviewed","feeding_safety_status":"not_assessed",
                "feeding_record_status":"not_reviewed","feeding_record_evidence":[],
                "safety_grade":None,"source_scope":"taxonomy_only"})
            if len(rows)>=limit:break
        if data.get("endOfRecords"):break
    return family,rows,scanned
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--workers",type=int,default=8)
    ap.add_argument("--per-family",type=int,default=350)
    args=ap.parse_args()
    if not 1<=args.workers<=12 or not 1<=args.per_family<=1000:ap.error("workers 1..12; per-family 1..1000")
    known=existing();result=[];report=[];errors=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        tasks={pool.submit(family_records,f,args.per_family):f for f in FAMILIES}
        for future in concurrent.futures.as_completed(tasks):
            f=tasks[future]
            try:
                family,rows,scanned=future.result()
                result.extend(rows);report.append({"family":family,"retrieved":len(rows),"scanned":scanned})
                print(f, len(rows),flush=True)
            except Exception as e:errors.append({"family":f,"error":str(e)})
    if errors:
        dest=ROOT/"data/diverse_taxonomy_errors.json"
        dest.write_text(json.dumps(errors,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        raise SystemExit(f"{len(errors)} family queries failed; no output promoted; see {dest}")
    if not result:raise SystemExit("No accepted taxa returned; refusing empty output")
    unique={};dupes=0
    for r in sorted(result,key=lambda x:(x["scientific_name"].casefold(),x["taxon_id"])):
        key=r["scientific_name"].casefold()
        if key in known or key in unique:dupes+=1;continue
        unique[key]=r
    if not unique:raise SystemExit("No new unique taxa; refusing empty output")
    payload={"schema_version":"1.0","source":"GBIF species API; taxonomy only",
        "record_count":len(unique),"records":list(unique.values())}
    path=ROOT/"data/diverse_taxonomy_candidates.json"
    path.write_text(json.dumps(payload,ensure_ascii=False,separators=(",",":"))+"\n",encoding="utf-8")
    audit={"new_taxa":len(unique),"excluded_existing_or_duplicate":dupes,
           "families_requested":len(FAMILIES),"family_results":sorted(report,key=lambda x:x["family"]),
           "feeding_evidence_linked":0,"safety_grades_assigned":0}
    (ROOT/"data/diverse_taxonomy_audit.json").write_text(json.dumps(audit,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("NEW",len(unique),"NO SAFETY CLAIMS")
if __name__=="__main__":main()
