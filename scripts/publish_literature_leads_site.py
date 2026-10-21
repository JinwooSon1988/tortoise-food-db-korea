#!/usr/bin/env python3
"""Publish reviewed-as-LEADS (not feeding safety) literature references to the static site.
Run after local bulk discovery finishes. Existing curated grades remain untouched.
"""
import argparse,json,pathlib,subprocess,sys
def main():
 p=argparse.ArgumentParser()
 p.add_argument('--input',default='data/literature_leads_all.json')
 p.add_argument('--community',default='data/community_source_leads_v1.json')
 p.add_argument('--output',default='data/research_source_leads_index.json')
 p.add_argument('--max-per-taxon',type=int,default=5)
 p.add_argument('--git-commit',action='store_true')
 a=p.parse_args()
 src=pathlib.Path(a.input)
 if not src.exists():p.error('Bulk literature output missing; finish the search first')
 data=json.loads(src.read_text(encoding='utf-8'))
 if not data.get('records'):p.error('No research records in input; refusing empty publish')
 expected=data.get('counts',{}); total=len(data['records'])
 if total<1000:p.error(f'Only {total} taxa searched; refusing premature mass publication')
 if expected and sum(int(expected.get(k,0)) for k in ('leads_found','no_leads_found','search_error'))!=total:p.error('Search counts do not match record count')
 if any(r.get('status')=='search_error' for r in data['records']):print('NOTICE: Some searches failed; those taxa require retries',file=sys.stderr)
 if a.max_per_taxon<1 or a.max_per_taxon>100:p.error('max-per-taxon must be 1..100')
 failed=sum(x.get('status')=='search_error' for x in data['records'])
 if failed:print(f'WARNING: {failed} taxon searches failed; do not treat absent leads as no evidence',file=sys.stderr)
 # Only publish records for real catalog taxa; do not trust arbitrary external IDs.
 catalog=pathlib.Path('data/plant-catalog')
 known_ids=set()
 for shard in sorted(catalog.glob('taxa-*.json')):
  for plant in json.loads(shard.read_text(encoding='utf-8')).get('records',[]):
   known_ids.add(str(plant.get('id','')))
 if not known_ids:p.error('Plant catalog is unavailable; refusing publication')
 taxa={};lit=0;comm=0;unknown_ids=0
 for r in data['records']:
  key=str(r.get('taxon_id',''))
  if key not in known_ids:
   unknown_ids+=1
   continue
  items=[];seen=set()
  for x in r.get('literature_leads',[]):
   doi=str(x.get('doi') or '').strip()
   source=str(x.get('source') or 'MED')
   pid=str(x.get('pmid') or '').strip()
   url='https://doi.org/'+doi if doi else ('https://europepmc.org/article/'+source+'/'+pid if pid else '')
   title=str(x.get('title') or '').strip()
   if not url or not title or url in seen or not url.startswith('https://'):continue
   seen.add(url)
   items.append({'title':title[:400],'year':str(x.get('pubYear') or '')[:8],'url':url,'verification':'search_hit_unreviewed','feeding_safety_status':'unassessed'})
   if len(items)>=a.max_per_taxon:break
  if items:
   taxa[key]={'literature_leads':items,'community_mentions':[]}
   lit+=len(items)
 community_file=pathlib.Path(a.community)
 if community_file.exists():
  c=json.loads(community_file.read_text(encoding='utf-8'))
  names={}
  catalog=pathlib.Path('data/plant-catalog')
  for shard in sorted(catalog.glob('taxa-*.json')):
   for r in json.loads(shard.read_text(encoding='utf-8')).get('records',[]):
    name=str(r.get('scientific','')).strip().casefold()
    names.setdefault(name,[]).append(r.get('id'))
  for x in c.get('records',[]):
   ids=names.get(str(x.get('plant_name_reported','')).strip().casefold(),[])
   if len(ids)!=1:continue
   url=str(x.get('source_url') or '')
   if not url.startswith('https://'):continue
   record=taxa.setdefault(ids[0],{'literature_leads':[],'community_mentions':[]})
   if any(y['source_url']==url for y in record['community_mentions']):continue
   record['community_mentions'].append({'source_url':url,'source_type':x.get('source_type'),'verification':'community_claim_not_independently_verified','feeding_safety_status':'unassessed'})
   comm+=1
 output={'schema_version':'1.0','warning':'Search leads and community mentions only; not proof of safe feeding.','taxa':taxa}
 if not taxa:p.error('No valid matched literature or community sources; refusing to replace index')
 target=pathlib.Path(a.output);target.parent.mkdir(parents=True,exist_ok=True)
 target.write_text(json.dumps(output,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
 print('Indexed taxa:',len(taxa),'Literature leads:',lit,'Community mentions:',comm,'Unmatched IDs:',unknown_ids,'Bytes:',target.stat().st_size)
 if a.git_commit:
  subprocess.run(['git','add','--',str(target).replace('\\','/')],check=True)
  diff=subprocess.run(['git','diff','--cached','--quiet','--',str(target).replace('\\','/')])
  if diff.returncode==1:
   subprocess.run(['git','commit','-m','Publish unreviewed literature leads with source links and safety caveats'],check=True)
   print('Commit created locally. Push after reviewing repository state: git push origin HEAD:main')
  elif diff.returncode==0:print('No changes to commit')
  else:raise RuntimeError('git diff failed')
if __name__=='__main__':main()
