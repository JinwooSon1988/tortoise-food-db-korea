#!/usr/bin/env python3
"""Audit every published plant evidence link for taxonomic and feeding-review precision."""
import argparse,json
from collections import Counter,defaultdict
from pathlib import Path

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",default="data/plant_feeding_evidence_links.json")
    p.add_argument("--output",default="data/evidence-review-shards/feeding-evidence-triage.json")
    args=p.parse_args()
    data=json.loads(Path(args.input).read_text(encoding="utf-8"))
    seen=set()
    rows=[]
    for plant in data["records"]:
        pid=plant["plant_id"]
        for e in plant.get("evidence",[]):
            key=(pid,e["evidence_id"])
            if key in seen:raise SystemExit("duplicate plant evidence id: "+str(key))
            seen.add(key)
            direct=e.get("directness","unspecified")
            applicability=e.get("applicability","unspecified")
            source_type=e.get("type","unspecified")
            tortoise=e.get("tortoise_taxon","unspecified")
            reported=e.get("plant_taxon_reported","")
            # No string matching can establish species identity or dietary safety.
            if source_type=="taxonomy_database":
                queue="taxonomy_context_only"
            elif direct in ("related_taxon","contextual") or applicability in ("taxon_group","composition_only"):
                queue="taxon_or_context_verification"
            elif tortoise in ("Tortoise general","not_applicable","unspecified"):
                queue="tortoise_species_verification"
            else:
                queue="primary_source_and_plant_part_verification"
            rows.append({"plant_id":pid,"scientific_name":plant.get("scientific_name"),
                "evidence_id":e["evidence_id"],"source_id":e.get("source_id"),
                "source_type":source_type,"directness":direct,"applicability":applicability,
                "tortoise_taxon_reported":tortoise,"plant_taxon_reported":reported,
                "plant_part_reported":e.get("plant_part"),
                "review_queue":queue,"content_verified":False,
                "feeding_safety_status":"not_assessed"})
    rows.sort(key=lambda r:(r["review_queue"],r["source_id"] or "",r["plant_id"],r["evidence_id"]))
    counts=dict(sorted(Counter(r["review_queue"] for r in rows).items()))
    by_source=defaultdict(list)
    for row in rows:by_source[row["source_id"] or "missing"].append(row)
    source_batches=[]
    source_groups=sorted(by_source.items(),key=lambda item:(-len(item[1]),item[0]))
    for i in range(0,len(source_groups),25):
        chunk=source_groups[i:i+25]
        source_batches.append({"batch_id":f"feeding-source-review-{i//25+1:03d}",
            "source_count":len(chunk),"evidence_count":sum(len(x) for _,x in chunk),
            "sources":[{"source_id":source,"evidence_count":len(evidence),
                "plant_ids":sorted({x["plant_id"] for x in evidence}),
                "review_queues":sorted({x["review_queue"] for x in evidence})}
                for source,evidence in chunk]})
    out={"scope":"triage only; not verification or feeding safety assessment",
        "plant_count":len(data["records"]),"evidence_count":len(rows),
        "unique_sources":len(by_source),"queue_counts":counts,
        "source_batch_count":len(source_batches),"source_batches":source_batches,"records":rows}
    target=Path(args.output);target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in out.items() if k not in ("records","source_batches")},ensure_ascii=False))
if __name__=="__main__":main()
