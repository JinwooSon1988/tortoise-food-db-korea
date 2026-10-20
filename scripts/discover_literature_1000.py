#!/usr/bin/env python3
"""Concurrent Europe PMC literature discovery for a 1000-taxon research queue.
Results are literature leads, NOT confirmed tortoise feeding or safety evidence.
Uses public API, caching, bounded parallelism, retry and resumable checkpoints.
"""
import argparse, concurrent.futures, json, pathlib, time, urllib.parse, urllib.request, urllib.error, threading
API='https://www.ebi.ac.uk/europepmc/webservices/rest/search'
LOCK=threading.Lock()
def lookup(item, cache, timeout):
 name=item['scientific']
 key=item['id']
 path=cache/(str(key).replace(':','_')+'.json')
 if path.exists():
  try:return json.loads(path.read_text(encoding='utf-8'))
  except (ValueError,OSError):pass
 # Exact botanical name AND tortoise context; relevance of hit requires original review.
 q='("'+name.replace('"','')+'") AND (tortoise OR Testudo OR Chelonoidis OR Geochelone OR Centrochelys OR Stigmochelys OR Gopherus OR Aldabrachelys)'
 url=API+'?'+urllib.parse.urlencode({'query':q,'format':'json','pageSize':5,'resultType':'core'})
 out={'taxon_id':key,'scientific':name,'query':q,'status':'search_error','literature_leads':[],'feeding_safety_status':'unassessed'}
 for attempt in range(3):
  try:
   req=urllib.request.Request(url,headers={'User-Agent':'GeobukbapEvidenceDiscovery/1.0 (public literature research)'})
   with urllib.request.urlopen(req,timeout=timeout) as res:data=json.load(res)
   hits=data.get('resultList',{}).get('result',[])
   out['status']='leads_found' if hits else 'no_leads_found'
   out['literature_leads']=[{'title':x.get('title',''),'authorString':x.get('authorString',''),'pubYear':x.get('pubYear',''),'doi':x.get('doi',''),'pmid':x.get('id',''),'source':x.get('source',''),'isOpenAccess':x.get('isOpenAccess',''),'verification':'search_hit_unreviewed','feeding_safety_status':'unassessed'} for x in hits]
   break
  except (urllib.error.URLError,TimeoutError,ValueError,OSError) as e:
   out['error']=str(e)[:200]
   if attempt<2:time.sleep(1.5*(attempt+1))
 if out['status']!='search_error':
  tmp=path.with_suffix('.tmp')
  with LOCK:
   tmp.write_text(json.dumps(out,ensure_ascii=False),encoding='utf-8')
   tmp.replace(path)
 return out
def main():
 p=argparse.ArgumentParser()
 p.add_argument('--input',default='data/research_priority_1000.json')
 p.add_argument('--out',default='data/literature_leads_1000.json')
 p.add_argument('--cache',default='data/research-cache/europepmc')
 p.add_argument('--workers',type=int,default=6)
 p.add_argument('--timeout',type=int,default=18)
 p.add_argument('--limit',type=int,default=1000)
 a=p.parse_args()
 if not 1<=a.workers<=8: p.error('workers must be 1..8 to avoid overloading public API')
 data=json.loads(pathlib.Path(a.input).read_text(encoding='utf-8'))
 items=data['records'][:a.limit]
 cache=pathlib.Path(a.cache);cache.mkdir(parents=True,exist_ok=True)
 results=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as pool:
  futures={pool.submit(lookup,item,cache,a.timeout):item for item in items}
  for f in concurrent.futures.as_completed(futures):
   try:results.append(f.result())
   except Exception as e:
    item=futures[f];results.append({'taxon_id':item['id'],'scientific':item['scientific'],'status':'search_error','error':str(e)[:200],'literature_leads':[]})
   if len(results)%100==0:print('Processed',len(results),'/',len(items),flush=True)
 results.sort(key=lambda x:x['scientific'].casefold())
 counts={k:sum(x['status']==k for x in results) for k in ['leads_found','no_leads_found','search_error']}
 counts['total_leads']=sum(len(x['literature_leads']) for x in results)
 counts['verified_feeding_records']=0
 output={'schema_version':'1.0','scope':'Unreviewed Europe PMC search hits; not feeding evidence or safety assessments','counts':counts,'records':results}
 dest=pathlib.Path(a.out);dest.parent.mkdir(parents=True,exist_ok=True)
 dest.write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(counts,ensure_ascii=False))
 print('Output:',dest)
if __name__=='__main__':main()
