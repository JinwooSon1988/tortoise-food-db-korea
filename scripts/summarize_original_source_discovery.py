#!/usr/bin/env python3
"""Aggregate saved bibliographic leads; never assign feeding or safety verdicts."""
import argparse,csv,json,pathlib,collections
ROOT=pathlib.Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--input',default='data/original-source-discovery');p.add_argument('--output',default='data/original-source-summary');a=p.parse_args()
 src=ROOT/a.input;out=ROOT/a.output;out.mkdir(parents=True,exist_ok=True)
 counts=collections.Counter();papers={};plant_hits=[];errors=[]
 files=sorted(src.glob('*.json'))
 for f in files:
  try:r=json.loads(f.read_text(encoding='utf-8'))
  except (OSError,ValueError) as e:errors.append({'file':f.name,'error':str(e)});continue
  status=r.get('status','unknown');counts['status_'+status]+=1
  name=r.get('scientific_name','')
  if status!='searched':
   errors.append({'file':f.name,'scientific_name':name,'error':r.get('error','unknown')});continue
  results=r.get('results',[]);counts['raw_paper_mentions']+=len(results)
  if results:counts['plants_with_search_hits']+=1
  else:counts['plants_without_search_hits']+=1
  for item in results:
   doi=str(item.get('doi') or '').strip().lower()
   source=str(item.get('source') or '').strip().lower()
   pid=str(item.get('pmid') or '').strip().lower()
   title=str(item.get('title') or '').strip().lower()
   key=('doi:'+doi) if doi else ('source:'+source+':'+pid if pid else 'title:'+title)
   if key not in papers:papers[key]={'title':item.get('title'),'doi':item.get('doi'),'source':item.get('source'),'record_id':item.get('pmid'),'pubYear':item.get('pubYear'),'journalTitle':item.get('journalTitle'),'isOpenAccess':item.get('isOpenAccess'),'matched_plants':set()}
   papers[key]['matched_plants'].add(name)
  if results:plant_hits.append({'scientific_name':name,'search_hits':len(results)})
 rows=[]
 for v in papers.values():
  v['matched_plants']=sorted(v['matched_plants']);rows.append(v)
 rows.sort(key=lambda x:(-len(x['matched_plants']),str(x['title'])))
 summary={'files_seen':len(files),'status_counts':dict(counts),'unique_bibliographic_leads':len(rows),'error_files':len(errors),'verified_direct_feeding_records':0,'note':'Search hits are unverified bibliographic leads, not evidence of consumption or safety.'}
 (out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 with (out/'paper_leads.jsonl').open('w',encoding='utf-8') as fh:
  for row in rows:fh.write(json.dumps(row,ensure_ascii=False)+'\n')
 with (out/'plant_hits.csv').open('w',encoding='utf-8',newline='') as fh:
  w=csv.DictWriter(fh,fieldnames=['scientific_name','search_hits']);w.writeheader();w.writerows(sorted(plant_hits,key=lambda x:-x['search_hits']))
 (out/'errors.json').write_text(json.dumps(errors,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
