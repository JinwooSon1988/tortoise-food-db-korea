#!/usr/bin/env python3
"""Bulk GBIF taxonomy intake: never infer tortoise feeding safety from taxonomy.
Usage: python scripts/build_global_taxonomy.py INPUT_CSV OUTPUT_JSON
"""
import csv,json,re,sys
from pathlib import Path

def main():
    if len(sys.argv)!=3: raise SystemExit("usage: build_global_taxonomy.py INPUT_CSV OUTPUT_JSON")
    source,target=map(Path,sys.argv[1:]);seen=set();ids=set();rows=[];reject=[]
    with source.open(encoding="utf-8-sig",newline="") as f:
        for line,r in enumerate(csv.DictReader(f),2):
            name=" ".join((r.get("scientific") or "").split())
            taxon=(r.get("gbif_taxon_key") or "").strip()
            if not re.fullmatch(r"[A-Z][a-z-]+ [a-z][a-z-]+",name) or not taxon.isdigit():
                reject.append({"line":line,"name":name,"reason":"not exact species binomial or missing GBIF key"});continue
            if name.casefold() in seen or taxon in ids:
                reject.append({"line":line,"name":name,"reason":"duplicate species or taxon key"});continue
            seen.add(name.casefold());ids.add(taxon)
            rows.append({"scientific_name":name,"family":r.get("family") or "",
                "source_taxon_url":"https://www.gbif.org/species/"+taxon,"taxon_id":"gbif:"+taxon,
                "identity_status":"taxonomy_candidate","feeding_evidence_status":"not_reviewed",
                "feeding_safety_status":"not_assessed","feeding_record_evidence":[],
                "safety_grade":None})
    rows.sort(key=lambda r:r["scientific_name"].casefold())
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps({"schema_version":"1.1","record_count":len(rows),"records":rows},ensure_ascii=False,separators=(",",":"))+"\n",encoding="utf-8")
    print(json.dumps({"accepted":len(rows),"rejected":len(reject),"target":str(target)},ensure_ascii=False))
    if reject:
        rejected_path=target.with_suffix(".rejected.json")
        rejected_path.write_text(json.dumps(reject,ensure_ascii=False,indent=2),encoding="utf-8")
    if not rows:raise SystemExit("no valid records")

if __name__=="__main__":main()
