#!/usr/bin/env python3
"""Parallel evidence-first discovery queue, preserving source context.

Reads verified repository sources, extracts only explicitly reported binomials,
cross-checks GBIF taxonomy candidate identities and reviewed plants, and writes
sharded review queues. A name mention is NOT a feeding record or safety verdict.
Usage: python scripts/parallel_evidence_first_queue.py --workers 20
"""
import argparse,concurrent.futures,hashlib,json,re
from collections import Counter,defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PAT=re.compile(r"(?<![A-Za-z])([A-Z][a-z]{2,})\s+([a-z][a-z-]{2,})(?![A-Za-z])")
STOP={"Tortoise","Testudo","Geochelone","Centrochelys","Stigmochelys","Chelonoidis","Gopherus","Kinixys","Indotestudo","Manouria","Agrionemys","Astrochelys","Pyxis","Homopus","Chersina","Psammobates","Malacochersus"}
def load(path):return json.loads((ROOT/path).read_text(encoding="utf-8"))
def canonical(s):
    m=PAT.search(str(s or ""))
    if not m or m.group(1) in STOP or m.group(2) in ("spp","sp","subsp","var","cf","aff"):return None
    return " ".join(m.groups())
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--workers",type=int,default=20)
    args=ap.parse_args()
    if not 1<=args.workers<=32:ap.error("workers must be 1..32")
    manifest=load("data/taxonomy-shards/index.json")
    diverse=load("data/diverse_taxonomy_candidates.json")
    if manifest.get("count")!=9995 or diverse.get("record_count")!=len(diverse.get("records",[])):
        raise SystemExit("taxonomy count mismatch")
    jobs=[("legacy-"+str(i+1).zfill(2),load("data/taxonomy-shards/"+sh["file"])["records"]) for i,sh in enumerate(manifest["shards"])]
    jobs.extend(("diverse-"+str(i//500+1).zfill(2),diverse["records"][i:i+500]) for i in range(0,len(diverse["records"]),500))
    def index(job):
        name,rows=job
        return name,{str(r.get("scientific_name","")).casefold():r for r in rows if canonical(r.get("scientific_name"))}
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        parts=list(pool.map(index,jobs))
    candidates={}
    for _,part in parts:candidates.update(part)
    plants=load("data/plants.json")
    reviewed={canonical(p.get("scientific")).casefold():p for p in plants if canonical(p.get("scientific"))}
    sources=load("data/public_evidence_records.json")["records"]
    links=load("data/plant_feeding_evidence_links.json")["records"]
    byid={p["id"]:p for p in plants}
    def from_source(e):
        out=[]
        # Only explicitly attributed plant taxa; titles can contain unrelated taxa.
        for field in ("plant_taxon","plant_taxon_reported"):
            raw=e.get(field)
            if not isinstance(raw,str):continue
            for match in PAT.finditer(raw):
                name=" ".join(match.groups())
                if match.group(1) not in STOP and match.group(2) not in ("spp","sp","subsp","var","cf","aff"):
                    out.append({"name":name,"field":field})
        return out
    def source_job(job):
        origin,entry=job
        if origin=="public":
            sid=entry.get("id");url=entry.get("url");type_="public_evidence"
            tortoise=entry.get("animal_taxon")
        else:
            sid=entry.get("evidence_id");url=entry.get("source_id");type_=entry.get("type")
            tortoise=entry.get("tortoise_taxon")
        return [{"scientific_name":v["name"],"source_id":sid,"source_url":url,
            "source_type":type_,"reported_field":v["field"],
            "tortoise_taxon_reported":tortoise,
            "evidence_state":"taxon_mention_unverified_feeding",
            "feeding_safety":"not_inferred"} for v in from_source(entry)]
    tasks=[("public",e) for e in sources]
    for rec in links:
        tasks.extend(("linked",dict(e,plant_taxon_reported=e.get("plant_taxon_reported",""))) for e in rec.get("evidence",[]))
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        extracted=list(pool.map(source_job,tasks))
    mentions=[v for group in extracted for v in group]
    grouped=defaultdict(list)
    for m in mentions:grouped[m["scientific_name"].casefold()].append(m)
    out=[]
    for name,refs in sorted(grouped.items()):
        candidate=candidates.get(name);plant=reviewed.get(name)
        unique={}
        for e in refs:
            ident=(e["source_id"],e["source_url"],e["reported_field"])
            unique[ident]=e
        out.append({"scientific_name":refs[0]["scientific_name"],
            "candidate_taxon_id":candidate.get("taxon_id") if candidate else None,
            "reviewed_plant_id":plant.get("id") if plant else None,
            "identity_status":"candidate_match" if candidate else ("reviewed_catalog" if plant else "identity_check_needed"),
            "mentions":list(unique.values()),
            "feeding_record_status":"requires_source_review",
            "feeding_safety_status":"not_assessed","safety_grade":None,
            "review_fields":["tortoise_species","plant_part","mixed_with","feeding_frequency","feeding_amount","presentation","cutting_method","source_quote_or_locator"]})
    folder=ROOT/"data/evidence-first-queue";folder.mkdir(exist_ok=True)
    manifest_out=[];counts=Counter()
    for stale in folder.glob("queue-*.json"):stale.unlink()
    for i in range(0,len(out),100):
        batch=out[i:i+100];fname="queue-"+str(i//100+1).zfill(3)+".json"
        raw=json.dumps({"schema_version":"1.0","count":len(batch),"records":batch},ensure_ascii=False,indent=2)+"\n"
        (folder/fname).write_text(raw,encoding="utf-8")
        manifest_out.append({"file":fname,"count":len(batch),"sha256":hashlib.sha256(raw.encode()).hexdigest()})
    counts["source_rows_processed"]=len(tasks)
    counts["taxon_mentions"]=len(mentions)
    counts["unique_taxa_mentioned"]=len(out)
    counts["matched_taxonomy_candidates"]=sum(bool(r["candidate_taxon_id"]) for r in out)
    counts["matched_reviewed_plants"]=sum(bool(r["reviewed_plant_id"]) for r in out)
    counts["identity_check_needed"]=sum(r["identity_status"]=="identity_check_needed" for r in out)
    audit={"schema_version":"1.0","disclaimer":"Evidence mentions are leads, not verified feeding records, feeding frequency, amount, or safety.","workers":args.workers,"counts":dict(counts),"shards":manifest_out}
    (folder/"index.json").write_text(json.dumps(audit,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(counts,ensure_ascii=False))
if __name__=="__main__":main()
