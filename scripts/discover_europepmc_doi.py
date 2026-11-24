#!/usr/bin/env python3
"""Discover DOI-matched Europe PMC records in parallel; no full-text or feeding claims."""
import argparse,concurrent.futures,json,time,urllib.error,urllib.parse,urllib.request
from pathlib import Path

def discover(row,timeout):
    doi=row.get("doi")
    result={"source_url":row["source_url"],"doi":doi,
            "linked_plant_ids":row["linked_plant_ids"],"status":"not_checked",
            "pmid":None,"pmcid":None,"is_open_access":None,
            "abstract_available":False,"error":None,
            "content_verified":False,"feeding_safety_status":"not_assessed"}
    if row.get("metadata_status")!="found" or not doi:return result
    query='DOI:"'+doi.replace('"','')+'"'
    endpoint="https://www.ebi.ac.uk/europepmc/webservices/rest/search?"+urllib.parse.urlencode(
        {"query":query,"format":"json","pageSize":5,"resultType":"core"})
    req=urllib.request.Request(endpoint,headers={"User-Agent":"GeobukbapResearch/1.0 (bibliography discovery)","Accept":"application/json"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req,timeout=timeout) as response:
                payload=json.load(response)
            matches=[r for r in payload.get("resultList",{}).get("result",[])
                     if str(r.get("doi","")).casefold()==doi.casefold()]
            if not matches:
                result["status"]="no_exact_doi_match"
            else:
                match=matches[0]
                result.update(status="exact_doi_match",pmid=match.get("id") if match.get("source")=="MED" else match.get("pmid"),
                    pmcid=match.get("pmcid"),is_open_access=match.get("isOpenAccess"),
                    abstract_available=bool(match.get("abstractText")))
            return result
        except urllib.error.HTTPError as exc:
            if exc.code in (429,500,502,503,504) and attempt<2:
                time.sleep(2*(attempt+1));continue
            result.update(status="lookup_failed",error="HTTP "+str(exc.code))
            return result
        except Exception as exc:
            if attempt<2:
                time.sleep(2*(attempt+1));continue
            result.update(status="lookup_failed",error=str(exc)[:200])
            return result
    return result

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--input",default="data/evidence-review-shards/doi-metadata-audit.json")
    ap.add_argument("--output",default="data/evidence-review-shards/europepmc-doi-discovery.json")
    ap.add_argument("--workers",type=int,default=2)
    ap.add_argument("--timeout",type=float,default=15)
    args=ap.parse_args()
    if not 1<=args.workers<=8 or not 1<=args.timeout<=30:ap.error("invalid limits")
    source=json.loads(Path(args.input).read_text(encoding="utf-8"))
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        records=list(pool.map(lambda row:discover(row,args.timeout),source["records"]))
    if len(records)!=source["count"]:raise SystemExit("source count mismatch")
    statuses=("exact_doi_match","no_exact_doi_match","lookup_failed","not_checked")
    summary={s:sum(r["status"]==s for r in records) for s in statuses}
    output={"scope":"DOI record discovery only; no article content verification or feeding assessment",
            "count":len(records),"summary":summary,
            "abstract_available_count":sum(r["abstract_available"] for r in records),
            "open_access_record_count":sum(r["is_open_access"]=="Y" for r in records),
            "records":records}
    path=Path(args.output);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in output.items() if k!="records"},ensure_ascii=False))
if __name__=="__main__":main()
