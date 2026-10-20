#!/usr/bin/env python3
"""Checkpointed parallel discovery of *leads*, never feeding/safety verdicts.

Uses Europe PMC public REST API; obey provider limits and preserve provenance.
Run from repository root: python scripts/parallel_original_source_discovery.py --workers 8
"""
import argparse, concurrent.futures, hashlib, json, pathlib, threading, time, urllib.parse, urllib.request
ROOT=pathlib.Path(__file__).resolve().parents[1]
LOCK=threading.Lock()
def fetch(name, timeout=25):
    query='("tortoise" OR "Testudo" OR "Geochelone" OR "Chelonoidis") AND "'+name.replace('"','')+'"'
    url='https://www.ebi.ac.uk/europepmc/webservices/rest/search?'+urllib.parse.urlencode({'query':query,'format':'json','pageSize':10})
    for attempt in range(4):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'GeobukbapEvidenceDiscovery/1.0 (research provenance)'})
            with urllib.request.urlopen(req,timeout=timeout) as response: data=json.load(response)
            return {'scientific_name':name,'query':query,'search_url':url,'status':'searched','results':[{'title':x.get('title'),'authorString':x.get('authorString'),'pubYear':x.get('pubYear'),'doi':x.get('doi'),'pmid':x.get('id'),'source':x.get('source'),'journalTitle':x.get('journalTitle'),'isOpenAccess':x.get('isOpenAccess')} for x in data.get('resultList',{}).get('result',[])],'review_status':'unverified_leads_only'}
        except Exception as exc:
            if attempt==3:return {'scientific_name':name,'search_url':url,'status':'error','error':str(exc),'results':[]}
            time.sleep(min(8,2**attempt))
def main():
    p=argparse.ArgumentParser();p.add_argument('--workers',type=int,default=8);p.add_argument('--limit',type=int,default=0);p.add_argument('--output',default='data/original-source-discovery');args=p.parse_args()
    if not 1<=args.workers<=20:p.error('workers must be 1..20')
    names=[]
    idx=json.loads((ROOT/'data/taxonomy-shards/index.json').read_text(encoding='utf-8'))
    for shard in idx['shards']:
        rows=json.loads((ROOT/'data/taxonomy-shards'/shard['file']).read_text(encoding='utf-8')).get('records',[])
        names.extend(r.get('scientific_name','').strip() for r in rows)
    names.extend(r.get('scientific_name','').strip() for r in json.loads((ROOT/'data/diverse_taxonomy_candidates.json').read_text(encoding='utf-8')).get('records',[]))
    names=list(dict.fromkeys(n for n in names if len(n.split())>=2))
    if args.limit:names=names[:args.limit]
    out=ROOT/args.output;out.mkdir(parents=True,exist_ok=True)
    def work(name):
        key=hashlib.sha256(name.casefold().encode()).hexdigest()
        dest=out/(key+'.json')
        if dest.exists():
            try:
                previous=json.loads(dest.read_text(encoding='utf-8'))
                if previous.get('status')=='searched':return 'cached'
            except (ValueError,OSError):pass
        result=fetch(name)
        temp=out/(key+'.tmp')
        temp.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        temp.replace(dest)
        return result['status']
    from collections import Counter
    counts=Counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        for status in pool.map(work,names):counts[status]+=1
    print(json.dumps({'unique_candidate_names':len(names),'counts':dict(counts),'verified_feeding_records':0,'note':'Bibliographic search leads only; original text and taxon identity require human review.'},ensure_ascii=False))
if __name__=='__main__':main()
