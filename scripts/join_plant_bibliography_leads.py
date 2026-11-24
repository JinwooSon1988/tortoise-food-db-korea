#!/usr/bin/env python3
"""Join Crossref bibliographic leads to published plant IDs, without safety promotion."""
import argparse,json
from collections import defaultdict,Counter
from pathlib import Path

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--queue",default="data/evidence-review-shards/global-source-review-queue.json")
    ap.add_argument("--metadata",default="data/evidence-review-shards/doi-metadata-audit.json")
    ap.add_argument("--output",default="data/evidence-review-shards/plant-bibliography-leads.json")
    args=ap.parse_args()
    queue=json.loads(Path(args.queue).read_text(encoding="utf-8"))
    audit=json.loads(Path(args.metadata).read_text(encoding="utf-8"))
    if queue["count"]!=len(queue["records"]) or audit["count"]!=len(audit["records"]):
        raise SystemExit("source count mismatch")
    sources={r["source_url"]:r for r in queue["records"]}
    if len(sources)!=len(queue["records"]):raise SystemExit("duplicate source URL")
    if {r["source_url"] for r in audit["records"]}!=set(sources):
        raise SystemExit("bibliography source set differs from evidence source set")
    byplant=defaultdict(list)
    for r in audit["records"]:
        src=sources[r["source_url"]]
        if r["metadata_status"]!="found":continue
        if r.get("content_verified") is not False or r.get("feeding_safety_status")!="not_assessed":
            raise SystemExit("bibliographic leads must remain unverified")
        for pid in src["linked_plant_ids"]:
            byplant[pid].append({
                "source_url":r["source_url"],"doi":r.get("doi"),
                "title":r.get("title"),"publication_year":r.get("publication_year"),
                "journal":r.get("journal"),"publisher":r.get("publisher"),
                "source_types":src.get("source_types",[]),
                "directness_types":src.get("directness_types",[]),
                "tortoise_taxa_reported":src.get("tortoise_taxa_reported",[]),
                "bibliographic_metadata_status":"found",
                "content_verified":False,"feeding_safety_status":"not_assessed",
                "review_status":"needs_full_text_and_taxon_verification"})
    records=[{"plant_id":pid,"bibliography_lead_count":len(rows),
              "bibliography_leads":sorted(rows,key=lambda x:x["source_url"])}
             for pid,rows in sorted(byplant.items())]
    out={"schema_version":"1.0","scope":"Crossref bibliography leads, not full-text or feeding safety verification",
         "source_count":queue["count"],
         "metadata_found_sources":sum(r["metadata_status"]=="found" for r in audit["records"]),
         "plant_count":len(records),
         "plant_source_links":sum(r["bibliography_lead_count"] for r in records),
         "records":records}
    # Group leads into deterministic review batches. Source reuse improves review efficiency,\n    # but does not imply direct feeding evidence or a safety recommendation.\n    review_sources=[]\n    audit_by_source={x["source_url"]:x for x in audit["records"]}\n    for source_url,src in sources.items():\n        meta=audit_by_source.get(source_url)\n        if not meta or meta["metadata_status"]!="found":continue\n        review_sources.append({"source_url":source_url,"doi":meta.get("doi"),\n            "title":meta.get("title"),"linked_plant_ids":src["linked_plant_ids"],\n            "linked_plant_count":len(src["linked_plant_ids"]),\n            "directness_types":src.get("directness_types",[]),\n            "tortoise_taxa_reported":src.get("tortoise_taxa_reported",[]),\n            "review_status":"needs_full_text_and_taxon_verification"})\n    review_sources.sort(key=lambda x:(-x["linked_plant_count"],x["source_url"]))\n    batches=[{"batch_id":f"bibliography-review-{i//25+1:03d}",\n              "source_count":len(review_sources[i:i+25]),\n              "records":review_sources[i:i+25]} for i in range(0,len(review_sources),25)]\n    review_out={"scope":"bibliographic leads only; no full-text or feeding safety verification",\n                "source_count":len(review_sources),"batch_count":len(batches),\n                "batches":batches}\n    review_path=Path(args.output).with_name("bibliography-review-batches.json")\n    review_path.parent.mkdir(parents=True,exist_ok=True)\n    review_path.write_text(json.dumps(review_out,ensure_ascii=False,indent=2)+"\\n",encoding="utf-8")\n    path=Path(args.output);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in out.items() if k!="records"},ensure_ascii=False))
if __name__=="__main__":main()
