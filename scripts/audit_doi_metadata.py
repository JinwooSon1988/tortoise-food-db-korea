#!/usr/bin/env python3
"""Bulk Crossref DOI metadata enrichment, without claiming source-content verification."""
import argparse,concurrent.futures,json,re,urllib.parse,urllib.request,urllib.error
from pathlib import Path

DOI_RE=re.compile(r"10\.\d{4,9}/[^\s?#]+",re.I)
def doi_from_url(url):
    p=urllib.parse.urlsplit(url)
    if p.hostname and p.hostname.lower() in ("doi.org","dx.doi.org"):
        doi=urllib.parse.unquote(p.path.lstrip("/"))
    else:
        m=DOI_RE.search(urllib.parse.unquote(url))
        doi=m.group(0) if m else ""
    return doi.rstrip(".,;") if DOI_RE.fullmatch(doi) else None

def lookup(row,timeout):
    url=row["source_url"];doi=doi_from_url(url)
    result={"source_url":url,"doi":doi,"linked_plant_ids":row["linked_plant_ids"],
            "metadata_status":"no_doi" if not doi else "lookup_failed",
            "title":None,"publication_year":None,"journal":None,"publisher":None,
            "crossref_type":None,"crossref_url":None,"error":None,
            "content_verified":False,"feeding_safety_status":"not_assessed"}
    if not doi:return result
    endpoint="https://api.crossref.org/works/"+urllib.parse.quote(doi,safe="")
    try:
        req=urllib.request.Request(endpoint,headers={"User-Agent":"GeobukbapResearch/1.0 (DOI metadata lookup)","Accept":"application/json"})
        with urllib.request.urlopen(req,timeout=timeout) as resp:
            payload=json.load(resp)["message"]
        dates=payload.get("published",{}).get("date-parts",[])
        result.update(metadata_status="found",title=(payload.get("title") or [None])[0],
            publication_year=dates[0][0] if dates and dates[0] else None,
            journal=(payload.get("container-title") or [None])[0],
            publisher=payload.get("publisher"),crossref_type=payload.get("type"),
            crossref_url=payload.get("URL"))
    except Exception as exc:result["error"]=str(exc)[:200]
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",default="data/evidence-review-shards/global-source-review-queue.json")
    p.add_argument("--output",default="data/evidence-review-shards/doi-metadata-audit.json")
    p.add_argument("--workers",type=int,default=12)
    p.add_argument("--timeout",type=float,default=8)
    a=p.parse_args()
    if not 1<=a.workers<=20 or not 1<=a.timeout<=30:p.error("invalid limits")
    records=json.loads(Path(a.input).read_text(encoding="utf-8"))["records"]
    with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as pool:
        results=list(pool.map(lambda r:lookup(r,a.timeout),records))
    counts={k:sum(r["metadata_status"]==k for r in results) for k in ("found","no_doi","lookup_failed")}
    data={"scope":"bibliographic metadata only; not full-text or feeding safety verification",
          "count":len(results),"summary":counts,"records":results}
    out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"count":len(results),"summary":counts}))
if __name__=="__main__":main()
