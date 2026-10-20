#!/usr/bin/env python3
"""Import manually collected, public community tortoise-feeding leads.
No platform scraping, login bypass or safety-grade inference. Python stdlib only.

CSV columns: url,platform,plant_scientific,tortoise_scientific,plant_part,
observation,source_title,observed_at,plant_identity,reviewer,notes
plant_identity: species_verified | name_reported | uncertain
observation: observed_eating | offered | husbandry_advice | plant_identification
"""
import argparse,csv,json,re,sys
from pathlib import Path
from urllib.parse import urlsplit
from datetime import datetime,timezone

FIELDS=('url','platform','plant_scientific','tortoise_scientific','plant_part','observation','source_title','observed_at','plant_identity','reviewer','notes')
PLATFORMS={'youtube','instagram','facebook','reddit','forum','blog','website','other'}
OBS={'observed_eating','offered','husbandry_advice','plant_identification'}
IDENTITY={'species_verified','name_reported','uncertain'}
def normalize(x): return re.sub(r'\s+',' ',(x or '').strip()).casefold()
def main():
 p=argparse.ArgumentParser()
 p.add_argument('--catalog',required=True,help='data/plant-catalog directory')
 p.add_argument('--input',required=True,help='CSV with individually sourced URLs')
 p.add_argument('--out',required=True,help='Output directory')
 a=p.parse_args()
 taxa={}
 for path in sorted(Path(a.catalog).glob('taxa-*.json')):
  for record in json.loads(path.read_text(encoding='utf-8'))['records']:
   taxa.setdefault(normalize(record['scientific']),[]).append(record)
 if not taxa: raise SystemExit('No catalog taxa found')
 linked=[];review=[];rejected=[];seen=set()
 with open(a.input,encoding='utf-8-sig',newline='') as fh:
  reader=csv.DictReader(fh)
  if not reader.fieldnames or any(k not in reader.fieldnames for k in FIELDS):
   raise SystemExit('Missing CSV columns: '+','.join(FIELDS))
  for line,row in enumerate(reader,2):
   url=(row['url'] or '').strip();parts=urlsplit(url)
   platform=normalize(row['platform']);observation=normalize(row['observation']);identity=normalize(row['plant_identity'])
   if parts.scheme!='https' or not parts.netloc or platform not in PLATFORMS or observation not in OBS or identity not in IDENTITY:
    rejected.append({'line':line,'reason':'invalid URL/platform/observation/identity','row':row});continue
   key=(url,normalize(row['plant_scientific']),normalize(row['tortoise_scientific']),observation)
   if key in seen:continue
   seen.add(key)
   matches=taxa.get(normalize(row['plant_scientific']),[])
   entry={'source_type':'community','url':url,'platform':platform,'source_title':row['source_title'].strip(),'plant_name_as_reported':row['plant_scientific'].strip(),'tortoise_name_as_reported':row['tortoise_scientific'].strip(),'plant_part':row['plant_part'].strip(),'observation':observation,'observed_at':row['observed_at'].strip(),'plant_identity':identity,'reviewer':row['reviewer'].strip(),'notes':row['notes'].strip(),'safety_grade':None,'feeding_safety_status':'unassessed','verification':'community_lead_not_independently_verified','imported_at':datetime.now(timezone.utc).date().isoformat()}
   # A reported name is NOT equivalent to a botanically verified identification.
   if len(matches)==1 and identity=='species_verified' and entry['reviewer'] and entry['source_title']:
    entry['taxon_id']=matches[0]['id'];entry['taxon_scientific']=matches[0]['scientific']
    entry['review_status']='identity_reviewed_source_pending';linked.append(entry)
   else:
    entry['review_status']='identity_or_source_review_needed'
    entry['catalog_matches']=len(matches)
    review.append(entry)
 out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
 for name,items in [('community_linked_candidates.json',linked),('community_review_queue.json',review),('community_rejected.json',rejected)]:
  (out/name).write_text(json.dumps(items,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'linked_candidates_not_approved':len(linked),'review_queue':len(review),'rejected':len(rejected)},ensure_ascii=False))
if __name__=='__main__':main()
