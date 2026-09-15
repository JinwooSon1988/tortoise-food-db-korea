from pathlib import Path
import json, subprocess
ROOT=Path(__file__).resolve().parents[1]
data=ROOT/'data'
plants_path=data/'plants.json'
plants=json.loads(plants_path.read_text(encoding='utf-8'))
if not any(x.get('id')=='lambs_lettuce' for x in plants):
    plants.append(json.loads((data/'master_69_lambs_lettuce.json').read_text(encoding='utf-8')))
plants_path.write_text(json.dumps(plants,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

cov_path=data/'coverage.json'; cov=json.loads(cov_path.read_text(encoding='utf-8'))
cov['plant_master_count']=69; cov['plants_with_explainable_assessment']=66
cov['master_review_accounting']={'assessed':66,'identity_blocked':2,'evidence_blocked':1,'total':69}
reviewed=cov.setdefault('priority_korea_foods_reviewed',[])
if 'lambs_lettuce' not in reviewed: reviewed.append('lambs_lettuce')
cov['pending_master_candidates']=[x for x in cov.get('pending_master_candidates',[]) if x!='lambs_lettuce']
cov['coverage_note']='66 of 69 master plants have structured assessments. Mallow and mint remain identity-blocked; minari remains evidence-blocked. General tortoise evidence is not promoted to Mediterranean Testudo direct evidence.'
cov['last_updated']='2026-09-16'
cov_path.write_text(json.dumps(cov,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

packet_path=data/'lambs_lettuce_candidate_packet.json'; packet=json.loads(packet_path.read_text(encoding='utf-8'))
packet.update({'integration_status':'promoted_to_master','published':True,'next_action':'complete','staging_status':'promoted_runtime'})
packet_path.write_text(json.dumps(packet,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

pc=ROOT/'profile-context.js'; s=pc.read_text(encoding='utf-8')
if "'_korea_addendum_12.json'" not in s: s=s.replace("'_korea_addendum_11.json']","'_korea_addendum_11.json','_korea_addendum_12.json']")
pc.write_text(s,encoding='utf-8')
sw=ROOT/'sw.js'; s=sw.read_text(encoding='utf-8')
if 'assessments_korea_addendum_12.json' not in s: s=s.replace("'./data/assessments_korea_addendum_11.json'","'./data/assessments_korea_addendum_11.json','./data/assessments_korea_addendum_12.json'")
if 'evidence_korea_addendum_12.json' not in s: s=s.replace("'./data/evidence_korea_addendum_11.json'","'./data/evidence_korea_addendum_11.json','./data/evidence_korea_addendum_12.json'")
sw.write_text(s,encoding='utf-8')
sm=ROOT/'sitemap.xml'; s=sm.read_text(encoding='utf-8'); url='https://jinwooson1988.github.io/tortoise-food-db-korea/plant/lambs_lettuce/'
if url not in s: s=s.replace('</urlset>',f'  <url><loc>{url}</loc></url>\n</urlset>')
sm.write_text(s,encoding='utf-8')
subprocess.run(['python','scripts/generate_static_pages.py'],cwd=ROOT,check=True)
for rel in ['plant/mallow/index.html','plant/sowthistle/index.html','plant/clover/index.html']:
    subprocess.run(['git','checkout','HEAD','--',rel],cwd=ROOT,check=True)
print('promoted lambs_lettuce; master',len(plants),'assessed',cov['plants_with_explainable_assessment'])
