#!/usr/bin/env python3
"""Audit Europe PMC discovery output and generate review queue. No automatic safety claims."""
import argparse,collections,csv,json,pathlib,re
def main():
 p=argparse.ArgumentParser();p.add_argument('--input',default='data/literature_leads_1000.json');p.add_argument('--out',default='data/literature_review_queue.csv');p.add_argument('--summary',default='data/literature_discovery_audit.json');a=p.parse_args()
 data=json.loads(pathlib.Path(a.input).read_text(encoding='utf-8'))
 rows=data.get('records',[]); queue=[];ids=set();duplicates=0
 for r in rows:
  for lead in r.get('literature_leads',[]):
   doi=(lead.get('doi') or '').strip().lower();pmid=str(lead.get('pmid') or '').strip()
   title=re.sub(r'\s+',' ',str(lead.get('title') or '')).strip()
   key=(r.get('scientific','').casefold(),doi or pmid or title.casefold())
   if key in ids:duplicates+=1;continue
   ids.add(key)
   queue.append({'plant_scientific':r.get('scientific',''),'taxon_id':r.get('taxon_id',''),'title':title,'year':lead.get('pubYear',''),'doi':doi,'source_id':pmid,'url':('https://doi.org/'+doi) if doi else ('https://europepmc.org/article/'+str(lead.get('source') or 'MED')+'/'+pmid if pmid else ''),'title_only_tortoise_context':'yes' if re.search(r'tortoise|testudo|chelon|geochel|gopherus|aldabra',title,re.I) else 'unknown','plant_name_in_title':'yes' if r.get('scientific','').casefold() in title.casefold() else 'no','review_status':'original_required','feeding_safety_status':'unassessed','tortoise_species_verified':'','plant_part_verified':'','actual_feeding_observed':'','reviewer':'','reviewed_at':''})
 queue.sort(key=lambda x:(x['plant_scientific'].casefold(),x['title'].casefold()))
 out=pathlib.Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
 with out.open('w',newline='',encoding='utf-8-sig') as f:
  w=csv.DictWriter(f,fieldnames=list(queue[0]) if queue else ['plant_scientific','taxon_id','title','year','doi','source_id','url','title_only_tortoise_context','plant_name_in_title','review_status','feeding_safety_status','tortoise_species_verified','plant_part_verified','actual_feeding_observed','reviewer','reviewed_at']);w.writeheader();w.writerows(queue)
 counts=collections.Counter(r.get('status','unknown') for r in rows)
 summary={'searched_taxa':len(rows),'unique_literature_leads':len(queue),'duplicate_taxon_literature_pairs':duplicates,'by_status':dict(counts),'plant_names_in_title':sum(x['plant_name_in_title']=='yes' for x in queue),'tortoise_context_in_title':sum(x['title_only_tortoise_context']=='yes' for x in queue),'verified_feeding_records_added':0,'note':'Search hits may mention a plant without documenting tortoise consumption; review originals before public evidence display.'}
 dest=pathlib.Path(a.summary);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(summary,ensure_ascii=False));print('Review queue:',out)
if __name__=='__main__':main()
