#!/usr/bin/env python3
"""Reconcile curated plants.json names against a WCVP DwC-A archive.

Exact binomial/infraspecific names are matched automatically.
Open genus-level entries (e.g. Taraxacum spp.) are explicitly retained as genus_scope
and are never coerced to one species.
"""
import argparse,csv,io,json,pathlib,re,zipfile
def norm(s):
 return re.sub(r"\s+"," ",(s or "").replace("×","×").strip()).casefold()
def main():
 ap=argparse.ArgumentParser();ap.add_argument("archive");ap.add_argument("--plants",default="data/plants.json");ap.add_argument("--output",default="data/reconciliation/curated69_wcvp.json");a=ap.parse_args()
 plants=json.loads(pathlib.Path(a.plants).read_text(encoding="utf-8"))
 exact={}; genera=set()
 wanted={norm(x["scientific"]) for x in plants if "spp." not in x["scientific"]}
 wanted_genera={norm(x["scientific"].split()[0]) for x in plants if "spp." in x["scientific"]}
 with zipfile.ZipFile(a.archive) as z:
  f=io.TextIOWrapper(z.open("wcvp_taxon.csv"),encoding="utf-8-sig",newline="")
  for r in csv.DictReader(f,delimiter="|"):
   n=norm(r["scientfiicname"])
   if n in wanted:
    exact.setdefault(n,[]).append({"wcvp_taxon_id":r["taxonid"],"wcvp_name":r["scientfiicname"],"authorship":r["scientfiicnameauthorship"] or None,"family":r["family"] or None,"rank":r["taxonrank"] or None,"status":r["taxonomicstatus"],"accepted_name_usage_id":r["acceptednameusageid"] or None,"scientific_name_id":r["scientificnameid"] or None,"reference":r["references"] or None})
   if norm(r["genus"]) in wanted_genera and r["taxonrank"].casefold()=="genus": genera.add(norm(r["genus"]))
 out=[]
 for p in plants:
  sci=p["scientific"]; key=norm(sci)
  if "spp." in sci:
   g=norm(sci.split()[0]); out.append({"plant_id":p["id"],"curated_name":sci,"match_status":"genus_scope","wcvp_genus_present":g in genera,"automatic_species_resolution":False,"review_note":"Curated record intentionally spans multiple species; do not collapse to a single WCVP species."});continue
  hits=exact.get(key,[])
  accepted=[h for h in hits if h["status"] in ("Accepted","Provisionally Accepted")]
  status="exact_unique_accepted" if len(accepted)==1 else ("exact_needs_review" if hits else "no_exact_match")
  out.append({"plant_id":p["id"],"curated_name":sci,"match_status":status,"matches":hits,"automatic_species_resolution":len(accepted)==1})
 q=pathlib.Path(a.output);q.parent.mkdir(parents=True,exist_ok=True);q.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 from collections import Counter
 print(json.dumps(Counter(x["match_status"] for x in out),ensure_ascii=False))
if __name__=="__main__":main()
