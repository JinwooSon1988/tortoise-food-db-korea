from pathlib import Path
import json, subprocess

ROOT=Path(__file__).resolve().parents[1]
data=ROOT/'data'

plants_path=data/'plants.json'
plants=json.loads(plants_path.read_text(encoding='utf-8'))
if not any(p.get('id')=='chard' for p in plants):
    plants.append({
      'id':'chard','ko':'근대','en':'Chard / Swiss Chard','scientific':'Beta vulgaris subsp. cicla','family':'Amaranthaceae',
      'category':'leafy','market':'마트/시장/온라인/재배','aliases':['스위스차드','Swiss chard','chard'],
      'identity_status':'verified_name','suitability_status':'unreviewed'
    })
plants_path.write_text(json.dumps(plants,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

cov_path=data/'coverage.json'; cov=json.loads(cov_path.read_text(encoding='utf-8'))
cov['plant_master_count']=68
cov['plants_with_explainable_assessment']=65
reviewed=cov.setdefault('priority_korea_foods_reviewed',[])
if 'chard' not in reviewed: reviewed.append('chard')
cov['master_review_accounting']={'assessed':65,'identity_blocked':2,'evidence_blocked':1,'total':68}
cov['pending_master_candidates']=[x for x in cov.get('pending_master_candidates',[]) if x!='chard']
cov['coverage_note']='65 of 68 master plants have structured assessments. The remaining three are intentionally blocked rather than guessed: mallow and mint require identity refinement, and minari lacks exact-taxon tortoise evidence. General reptile or tortoise evidence is not promoted to Mediterranean Testudo direct evidence.'
cov['last_updated']='2026-09-16'
cov_path.write_text(json.dumps(cov,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

# Mark staging records as promoted so metadata cannot contradict runtime state.
cp=data/'chard_candidate_packet.json'; packet=json.loads(cp.read_text(encoding='utf-8'))
packet.update({'integration_status':'promoted_to_master','runtime_promotion_requires_master':False,'staging_changes_user_facing_verdict':True,'next_action':'complete','published':True})
cp.write_text(json.dumps(packet,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
ca=data/'chard_candidate_assessment.json'; staged=json.loads(ca.read_text(encoding='utf-8'))
staged.update({'status':'promoted_runtime','runtime_promotion_requires_master':False,'user_facing':True,'ready_for_atomic_promotion':False})
ca.write_text(json.dumps(staged,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

pc=ROOT/'profile-context.js'; s=pc.read_text(encoding='utf-8')
if "'_korea_addendum_11.json'" not in s:
    s=s.replace("'_korea_addendum_10.json']","'_korea_addendum_10.json','_korea_addendum_11.json']")
pc.write_text(s,encoding='utf-8')

sw=ROOT/'sw.js'; s=sw.read_text(encoding='utf-8').replace("tfd-v51-stable-36","tfd-v51-stable-37")
if "assessments_korea_addendum_11.json" not in s:
    s=s.replace("'./data/assessments_korea_addendum_10.json'","'./data/assessments_korea_addendum_10.json','./data/assessments_korea_addendum_11.json'")
if "evidence_korea_addendum_11.json" not in s:
    s=s.replace("'./data/evidence_korea_addendum_10.json'","'./data/evidence_korea_addendum_10.json','./data/evidence_korea_addendum_11.json'")
sw.write_text(s,encoding='utf-8')

sm=ROOT/'sitemap.xml'; s=sm.read_text(encoding='utf-8')
url='https://jinwooson1988.github.io/tortoise-food-db-korea/plant/chard/'
if url not in s:
    s=s.replace('</urlset>',f'  <url><loc>{url}</loc></url>\n</urlset>')
sm.write_text(s,encoding='utf-8')

subprocess.run(['python','scripts/generate_static_pages.py'],cwd=ROOT,check=True)
for rel in ['plant/mallow/index.html','plant/sowthistle/index.html','plant/clover/index.html']:
    subprocess.run(['git','checkout','HEAD','--',rel],cwd=ROOT,check=True)
print('promoted chard; master',len(plants),'assessed',cov['plants_with_explainable_assessment'])
