#!/usr/bin/env python3
"""Concurrent source URL reachability audit. Never asserts feeding safety."""
import argparse,concurrent.futures,json,ipaddress,socket,urllib.error,urllib.parse,urllib.request
from pathlib import Path

def check(row,timeout):
    url=row["source_url"]
    result={"source_url":url,"linked_plant_ids":row["linked_plant_ids"],
            "status":"unreachable","http_status":None,"final_url":None,
            "content_type":None,"error":None,"review_status":"not_verified","method":"HEAD"}
    try:
        parsed=urllib.parse.urlsplit(url)
        if parsed.scheme not in ("http","https") or not parsed.hostname:
            raise ValueError("unsupported URL")
        addresses=socket.getaddrinfo(parsed.hostname,None)
        if not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses):
            raise ValueError("non-public destination")
        req=urllib.request.Request(url,headers={"User-Agent":"GeobukbapEvidenceAudit/1.0 (research-only)","Accept":"text/html,application/pdf,*/*;q=0.1"},method="HEAD")
        # Disable redirects: redirect targets require independent address validation.
        opener=urllib.request.build_opener(type("NoRedirect",(urllib.request.HTTPRedirectHandler,),{"redirect_request":lambda self,*a:None})())
        try:
            response=opener.open(req,timeout=timeout)
        except urllib.error.HTTPError as e:
            response=e
        if response.status in (403,405,501):
            response.close()
            result["method"]="GET"
            req=urllib.request.Request(url,headers={"User-Agent":"GeobukbapEvidenceAudit/1.0 (research-only)","Accept":"text/html,application/pdf,*/*;q=0.1","Range":"bytes=0-0"},method="GET")
            try:
                response=opener.open(req,timeout=timeout)
            except urllib.error.HTTPError as e:
                response=e
        with response:
            result["http_status"]=response.status
            result["content_type"]=response.headers.get("Content-Type")
            result["final_url"]=response.url
            result["status"]="reachable" if 200<=response.status<300 else ("redirect_needs_review" if 300<=response.status<400 else "http_error")
    except Exception as e:
        result["error"]=str(e)[:250]
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",default="data/evidence-review-shards/global-source-review-queue.json")
    p.add_argument("--output",default="data/evidence-review-shards/live-source-url-audit.json")
    p.add_argument("--workers",type=int,default=12)
    p.add_argument("--timeout",type=float,default=8)
    a=p.parse_args()
    if not 1<=a.workers<=20 or not 1<=a.timeout<=30:p.error("invalid limits")
    rows=json.loads(Path(a.input).read_text(encoding="utf-8"))["records"]
    with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as pool:
        results=list(pool.map(lambda row:check(row,a.timeout),rows))
    summary={status:sum(r["status"]==status for r in results) for status in ("reachable","redirect_needs_review","http_error","unreachable")}
    output={"schema_version":"1.0","scope":"URL reachability only; not content or feeding-safety verification",
            "count":len(results),"summary":summary,"records":results}
    dest=Path(a.output);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"count":len(results),"summary":summary}))
if __name__=="__main__":main()
