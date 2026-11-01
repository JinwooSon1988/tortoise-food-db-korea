#!/usr/bin/env python3
"""Select 1,000 distinct GBIF plant taxa for evidence research; never assign feeding safety."""
import argparse, json, pathlib, hashlib
from collections import Counter
def main():
 p=argparse.ArgumentParser();p.add_argument('--catalog',default='data/plant-catalog');p.add_argument('--out',default='data/research_priority_1000.json');p.add_argument('--limit',type=int,default=0,help='0 selects all unique catalog taxa');p.add_argument('--shards',type=int,default=0,help='0 disables sharding; 1..128 produces deterministic parallel research batches');a=p.parse_args()\n if not 0<=a.shards<=128: p.error('--shards must be 0..128')
 root=pathlib.Path(a.catalog); taxa=[]
 for file in sorted(root.glob('taxa-*.json')):
  doc=json.loads(file.read_text(encoding='utf-8'))
  taxa.extend(doc.get('records',[]))
 if not taxa: raise SystemExit('No catalog shards found')
 seen=set(); ranked=[]
 for r in taxa:
  name=str(r.get('scientific','')).strip();key=name.casefold()
  if not name or key in seen:continue
  seen.add(key)
  research=r.get('research') or {}
  ev=r.get('feeding_evidence') or []
  common=r.get('common_names') or {}
  ko=common.get('ko') or []
  en=common.get('en') or []
  if isinstance(ko,str):ko=[ko]
  if isinstance(en,str):en=[en]
  # Research prioritization only: evidence leads, local name, international name, stable ID.
  status=research.get('status','no_record_found')
  score=(100 if ev else 0)+(30 if status!='no_record_found' else 0)+(12 if ko else 0)+(4 if en else 0)
  ranked.append(( -score,name.casefold(),str(r.get('id','')),r, status,len(ev)))
 ranked.sort(key=lambda t:(t[0],t[1],t[2]))
 chosen=[]
 for _,_,_,r,status,n in ranked if a.limit==0 else ranked[:a.limit]:
  chosen.append({'id':r.get('id'),'scientific':r.get('scientific'),'family':r.get('family'),'research_status':status,'linked_evidence_count':n,'feeding_safety_status':'unassessed','review_status':'research_required'})
 if a.limit and len(chosen)<a.limit:raise SystemExit(f'Only {len(chosen)} unique taxa found; expected {a.limit}')
 out={'schema_version':'1.0','description':'Research queue, not feeding recommendations. GBIF taxonomy alone never establishes feeding safety.','selection':'Existing linked evidence first; Korean and English common names then scientific name','target_count':len(chosen),'records':chosen}
 dest=pathlib.Path(a.out);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 if a.shards:
  shard_dir=dest.parent/(dest.stem+'_shards')
  shard_dir.mkdir(parents=True,exist_ok=True)
  batches=[[] for _ in range(a.shards)]
  for record in chosen:
   # Stable across input order, worker count and repeated runs; never assign feeding safety.
   identity=str(record.get('id') or record['scientific']).encode('utf-8')
   idx=int.from_bytes(hashlib.sha256(identity).digest()[:8],'big')%a.shards
   batches[idx].append(record)
  manifest=[]
  for idx,records in enumerate(batches):
   records.sort(key=lambda r:(str(r['scientific']).casefold(),str(r.get('id'))))
   filename=f'batch-{idx:03d}.json'
   payload={'schema_version':'1.0','batch_index':idx,'batch_count':a.shards,'target_count':len(records),'feeding_safety_status':'unassessed','records':records}
   (shard_dir/filename).write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\\n',encoding='utf-8')
   manifest.append({'file':filename,'count':len(records)})
  if sum(b['count'] for b in manifest)!=len(chosen):
   raise SystemExit('Batch partition failed: lost or duplicated research candidates')
  (shard_dir/'manifest.json').write_text(json.dumps({'schema_version':'1.0','source':str(dest),'total':len(chosen),'batch_count':a.shards,'batches':manifest,'safety_grades_assigned':0},ensure_ascii=False,indent=2)+'\\n',encoding='utf-8')
  print(f'Partitioned {len(chosen)} unique taxa into {a.shards} deterministic research batches: {shard_dir}')
 print(f'Wrote {len(chosen)} research candidates to {dest}; feeding grades assigned: 0')
if __name__=='__main__':main()
