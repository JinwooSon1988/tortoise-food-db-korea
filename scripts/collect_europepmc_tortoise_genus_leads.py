#!/usr/bin/env python3
"""Batch-search Europe PMC for tortoise diet literature across candidate genera.

Run on Google Colab/local Python (not GitHub Actions). Literature metadata and
abstracts are DISCOVERY LEADS, never verified feeding or safety evidence.
"""
import argparse, csv, json, time, urllib.parse, urllib.request
from collections import defaultdict
from pathlib import Path

API="https://www.ebi.ac.uk/europepmc/webservices/rest/search"
TORTOISE='(tortoise OR Testudo OR Gopherus OR Chelonoidis OR Centrochelys OR Stigmochelys OR Geochelone OR Aldabrachelys OR Astrochelys OR Manouria OR Indotestudo OR Kinixys)'
def get(q, page_size):
    params=urllib.parse.urlencode({"query":q,"format":"json","pageSize":page_size,"resultType":"core"})
    request=urllib.request.Request(API+"?"+params,headers={"User-Agent":"geobukbap-evidence-discovery/1.0"})
    with urllib.request.urlopen(request,timeout=45) as response:
        return json.load(response)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--crosswalk",type=Path,required=True)
    ap.add_argument("--out",type=Path,default=Path("research/generated/europepmc_tortoise_genus_leads.json"))
    ap.add_argument("--limit-genera",type=int,default=0,help="0 means all genera")
    ap.add_argument("--page-size",type=int,default=25)
    ap.add_argument("--delay",type=float,default=0.4)
    args=ap.parse_args()
    by_genus=defaultdict(list)
    with args.crosswalk.open(encoding="utf-8-sig",newline="") as fh:
        for r in csv.DictReader(fh):
            sci=r.get("scientific","").split()
            if len(sci)>=2:
                by_genus[sci[0]].append(r["scientific"])
    genera=sorted(by_genus,key=lambda g:(-len(by_genus[g]),g))
    if args.limit_genera>0:genera=genera[:args.limit_genera]
    args.out.parent.mkdir(parents=True,exist_ok=True)
    results={"schema_version":"1.0","warning":"Bibliography discovery only. Never use these results to infer plant safety, feeding verdicts, exact animal taxa, or consumed plant parts.","queried_genera":genera,"results":[]}
    for i,genus in enumerate(genera,1):
        query=f'{TORTOISE} AND ("{genus}") AND (diet OR feeding OR forage OR food OR herbivory)'
        try:
            payload=get(query,args.page_size)
            items=[]
            for paper in payload.get("resultList",{}).get("result",[]):
                items.append({"title":paper.get("title"),"year":paper.get("pubYear"),
                    "doi":paper.get("doi"),"pmid":paper.get("pmid"),"pmcid":paper.get("pmcid"),
                    "abstract":paper.get("abstractText"),"source":paper.get("journalTitle"),
                    "url":"https://europepmc.org/article/"+str(paper.get("source","MED"))+"/"+str(paper.get("id","")),
                    "verified_feeding_evidence":False})
            entry={"genus":genus,"candidate_taxa":len(by_genus[genus]),"hit_count":int(payload.get("hitCount",0)),
                   "papers":items,"search_query":query}
        except Exception as exc:
            entry={"genus":genus,"candidate_taxa":len(by_genus[genus]),"error":str(exc),"papers":[]}
        results["results"].append(entry)
        # Save after each genus to preserve partial work on free Colab disconnect.
        args.out.write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding="utf-8")
        if i%25==0:print(f"Queried {i}/{len(genera)} genera, {sum(len(x['papers']) for x in results['results'])} paper leads")
        time.sleep(max(0,args.delay))
    print(json.dumps({"genera":len(genera),"papers":sum(len(x["papers"]) for x in results["results"]),
                      "errors":sum("error" in x for x in results["results"]),"out":str(args.out)},ensure_ascii=False))
if __name__=="__main__":main()
