#!/usr/bin/env python3
"""Parallel reverse join: begin from evidence plant IDs, not random GBIF candidates.

Retains all 182 reviewed plant identities as a distinct catalog; matches candidate
taxa only on unambiguous species binomials. Genus evidence remains contextual.
No grades or unreported feeding practices are inferred.
"""
import concurrent.futures,json,re,argparse
from collections import defaultdict,Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads((ROOT/p).read_text(encoding="utf-8"))
def key(s):
    m=re.match(r"^([A-Z][a-z-]+)\s+([a-z][a-z-]+)(?=\s|$)",str(s or "").strip())
    return " ".join(m.groups()).casefold() if m else None
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--workers",type=int,default=12)
    args=ap.parse_args()
    if not 1<=args.workers<=20:ap.error("workers 1..20")
    plants=read("data/plants.json")
    sources=read("data/public_evidence_records.json")["records"]
    linkfile=read("data/plant_feeding_evidence_links.json")
    links=linkfile["records"]
    byid={p["id"]:p for p in plants}
    if len(byid)!=len(plants):raise SystemExit("duplicate reviewed plant IDs")
    src=defaultdict(list)
    for e in sources:
        for pid in e.get("plant_ids",[]):
            if pid in byid:src[pid].append(e)
    joined=defaultdict(list)
    for r in links:
        if r["plant_id"] in byid:joined[r["plant_id"]].extend(r.get("evidence",[]))
    # Work on existing verified catalog, regardless of random candidate sampling.
    def work(p):
        pid=p["id"];k=key(p.get("scientific"))
        docs=src.get(pid,[])
        refs=joined.get(pid,[])
        wild=[e for e in refs if e.get("type")=="wild_feeding" and
              e.get("directness") in ("direct","exact_species") and
              key(e.get("plant_taxon_reported"))==k and
              e.get("source_id") and e.get("tortoise_taxon")]
        return {"plant_id":pid,"scientific_name":p.get("scientific"),
          "family":p.get("family"),"source_count":len(docs),
          "linked_reference_count":len(refs),
          "direct_species_wild_feeding_under_review":len(wild),
          "public_sources":[{"id":e.get("id"),"title":e.get("source_title"),
             "url":e.get("url"),"animal_taxon":e.get("animal_taxon"),
             "plant_taxon_reported":e.get("plant_taxon"),
             "plant_part_reported":e.get("plant_part_state"),
             "directness":e.get("directness"),"supports":e.get("supports"),
             "limitations":e.get("does_not_support")} for e in docs],
          "wild_feeding_sources":[{"source_id":e.get("source_id"),
             "tortoise_taxon":e.get("tortoise_taxon"),
             "plant_part":e.get("plant_part")} for e in wild],
          "safety_grade_inferred":False}
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        records=list(pool.map(work,plants))
    counts=Counter()
    for r in records:
        counts["reviewed_plants"]+=1
        counts["plants_with_public_sources"]+=bool(r["source_count"])
        counts["plants_with_linked_references"]+=bool(r["linked_reference_count"])
        counts["plants_with_direct_wild_record_under_review"]+=bool(r["direct_species_wild_feeding_under_review"])
        counts["public_source_joins"]+=r["source_count"]
        counts["reference_joins"]+=r["linked_reference_count"]
    dest=ROOT/"data/reviewed_plant_reverse_evidence_index.json"
    dest.write_text(json.dumps({"schema_version":"1.0","purpose":"reverse evidence joins, not safety promotion",
       "counts":dict(counts),"records":records},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(counts,ensure_ascii=False))
if __name__=="__main__":main()
