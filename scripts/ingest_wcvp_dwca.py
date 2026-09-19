#!/usr/bin/env python3
"""Stream Kew WCVP DwC-A into compact candidate shards without loading the archive into RAM."""
import argparse,csv,io,json,pathlib,zipfile
from collections import Counter
def main():
 p=argparse.ArgumentParser();p.add_argument("archive");p.add_argument("--outdir",default="data/staging/wcvp");p.add_argument("--shard-size",type=int,default=50000);a=p.parse_args()
 out=pathlib.Path(a.outdir);out.mkdir(parents=True,exist_ok=True)
 counts=Counter(); shard=[]; shard_no=0
 def flush():
  nonlocal shard,shard_no
  if not shard:return
  q=out/f"taxa-{shard_no:04d}.jsonl";q.write_text("".join(json.dumps(x,ensure_ascii=False,separators=(",",":"))+"\n" for x in shard),encoding="utf-8");shard=[];shard_no+=1
 with zipfile.ZipFile(a.archive) as z:
  f=io.TextIOWrapper(z.open("wcvp_taxon.csv"),encoding="utf-8-sig",newline="")
  r=csv.DictReader(f,delimiter="|")
  for x in r:
   status=x["taxonomicstatus"]; counts[status]+=1
   shard.append({"source_id":"kew_wcvp","source_record_id":x["taxonid"],"scientific_name":x["scientfiicname"],"authorship":x["scientfiicnameauthorship"] or None,"family":x["family"] or None,"genus":x["genus"] or None,"rank":x["taxonrank"] or None,"taxonomic_status":status,"accepted_source_record_id":x["acceptednameusageid"] or None,"parent_source_record_id":x["parentnameusageid"] or None,"scientific_name_id":x["scientificnameid"] or None,"reference_url":x["references"] or None,"feed_review_status":"identity_only"})
   if len(shard)>=a.shard_size:flush()
  flush()
 manifest={"source_id":"kew_wcvp","taxon_rows":sum(counts.values()),"taxonomic_status_counts":dict(counts),"shards":shard_no,"distribution_file":"wcvp_distribution.csv","replacement_names_file":"wcvp_replacementNames.csv","feeding_interpretation":"none; taxonomy identity only"}
 (out/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps(manifest,ensure_ascii=False))
if __name__=="__main__":main()
