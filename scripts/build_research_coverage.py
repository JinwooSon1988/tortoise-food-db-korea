#!/usr/bin/env python3
"""Join taxon catalog, literature leads, and community mentions without inventing feeding grades.
Creates an evidence coverage report and per-taxon source-lead index for editorial review.
"""
import argparse,collections,json,pathlib
def main():
 p=argparse.ArgumentParser()
 p.add_argument('--catalog',default='data/plant-catalog')
 p.add_argument('--literature',default='data/literature_leads_all.json')
 p.add_argument('--community',default='data/community_source_leads_v1.json')
 p.add_argument('--out',default='data/research_coverage_report.json')
 p.add_argument('--index-out',default='data/research_source_leads_index.json')
 a=p.parse_args()
 records=[]
 for file in sorted(pathlib.Path(a.catalog).glob('taxa-*.json')):
  records.extend(json.loads(file.read_text(encoding='utf-8')).get('records',[]))
 if not records:raise SystemExit('Catalog missing')
 byname=collections.defaultdict(list)
 for r in records:byname[str(r.get('scientific','')).casefold().strip()].append(r)
 literature=json.loads(pathlib.Path(a.literature).read_text(encoding='utf-8')) if pathlib.Path(a.literature).exists() else {'records':[]}
 community=json.loads(pathlib.Path(a.community).read_text(encoding='utf-8')) if pathlib.Path(a.community).exists() else {'records':[]}
 sources=collections.defaultdict(lambda:{'literature_leads':[],'community_mentions':[]})
 unresolved=[]; unmatched=[]
 for r in literature.get('records',[]):
  key=r.get('taxon_id')
  if not key:continue
  for hit in r.get('literature_leads',[]):
   doi=str(hit.get('doi') or '').strip()
   src=str(hit.get('source') or 'MED')
   pid=str(hit.get('pmid') or '')
   url='https://doi.org/'+doi if doi else ('https://europepmc.org/article/'+src+'/'+pid if pid else '')
   sources[key]['literature_leads'].append({'title':hit.get('title',''),'year':hit.get('pubYear',''),'url':url,'verification':'search_hit_unreviewed','feeding_safety_status':'unassessed'})
 for mention in community.get('records',[]):
  name=str(mention.get('plant_name_reported','')).casefold().strip()
  candidates=byname.get(name,[])
  if len(candidates)!=1:
   unmatched.append({'scientific':mention.get('plant_name_reported'),'matches':len(candidates),'source_url':mention.get('source_url')})
   continue
  item=candidates[0]
  sources[item['id']]['community_mentions'].append({'source_url':mention.get('source_url'),'source_type':mention.get('source_type'),'verification':'community_claim_not_independently_verified','feeding_safety_status':'unassessed'})
 stats=collections.Counter()
 for r in records:
  stats['catalog_taxa']+=1
  if r.get('feeding_evidence'):stats['existing_feeding_evidence_taxa']+=1
  s=sources.get(r['id'])
  if s and s['literature_leads']:stats['literature_lead_taxa']+=1
  if s and s['community_mentions']:stats['community_mention_taxa']+=1
  if s and (s['literature_leads'] or s['community_mentions']):stats['new_source_lead_taxa']+=1
  if r.get('feeding_evidence') or (s and (s['literature_leads'] or s['community_mentions'])):stats['any_evidence_or_lead_taxa']+=1
 stats['unmatched_community_mentions']=len(unmatched)
 stats['literature_lead_records']=sum(len(v['literature_leads']) for v in sources.values())
 stats['community_mention_records_matched']=sum(len(v['community_mentions']) for v in sources.values())
 stats['newly_verified_feeding_safety_taxa']=0
 index={'schema_version':'1.0','warning':'Literature hits and community mentions are unreviewed; never infer feeding safety or recommendations.','taxa':dict(sources)}
 report={'schema_version':'1.0','counts':dict(stats),'unmatched_community_mentions':unmatched,'literature_search_status':literature.get('counts',{}),'definitions':{'existing_feeding_evidence_taxa':'Catalog has at least one linked feeding observation or study, not necessarily feeding safety verification','literature_lead_taxa':'Unreviewed Europe PMC search hits','community_mention_taxa':'Forum mentions, may be toxic plant lists or identification questions','newly_verified_feeding_safety_taxa':'This script never verifies safety'}}
 for name,content in [(a.out,report),(a.index_out,index)]:
  path=pathlib.Path(name);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(content,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(report['counts'],ensure_ascii=False))
if __name__=='__main__':main()
