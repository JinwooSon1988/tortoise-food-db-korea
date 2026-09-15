from pathlib import Path
import json, subprocess

ROOT=Path(__file__).resolve().parents[1]
data=ROOT/'data'

plants_path=data/'plants.json'
plants=json.loads(plants_path.read_text(encoding='utf-8'))
if not any(p.get('id')=='dill' for p in plants):
    plants.append({
      'id':'dill','ko':'딜','en':'Dill','scientific':'Anethum graveolens','family':'Apiaceae',
      'category':'herb','market':'마트/온라인/재배','aliases':['딜잎','dill'],
      'identity_status':'verified_name','suitability_status':'reviewed'
    })
plants_path.write_text(json.dumps(plants,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

cov_path=data/'coverage.json'; cov=json.loads(cov_path.read_text(encoding='utf-8'))
cov['plant_master_count']=67
cov['plants_with_explainable_assessment']=64
reviewed=cov.setdefault('priority_korea_foods_reviewed',[])
if 'dill' not in reviewed: reviewed.append('dill')
cov['master_review_accounting']={'assessed':64,'identity_blocked':2,'evidence_blocked':1,'total':67}
cov['pending_master_candidates']=[x for x in cov.get('pending_master_candidates',[]) if x!='dill']
cov['coverage_note']='64 of 67 master plants have structured assessments. The remaining three are intentionally blocked rather than guessed: mallow and mint require identity refinement, and minari lacks exact-taxon tortoise evidence. General reptile or tortoise evidence is not promoted to Mediterranean Testudo direct evidence.'
cov['last_updated']='2026-09-15'
cov_path.write_text(json.dumps(cov,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

pc=ROOT/'profile-context.js'; s=pc.read_text(encoding='utf-8')
needle="'_korea_addendum_9.json']"
if "'_korea_addendum_10.json'" not in s:
    s=s.replace(needle,"'_korea_addendum_9.json','_korea_addendum_10.json']")
pc.write_text(s,encoding='utf-8')

sw=ROOT/'sw.js'; s=sw.read_text(encoding='utf-8').replace("tfd-v51-stable-35","tfd-v51-stable-36")
if "assessments_korea_addendum_10.json" not in s:
    s=s.replace("'./data/assessments_korea_addendum_9.json'","'./data/assessments_korea_addendum_9.json','./data/assessments_korea_addendum_10.json'")
if "evidence_korea_addendum_10.json" not in s:
    s=s.replace("'./data/evidence_korea_addendum_9.json'","'./data/evidence_korea_addendum_9.json','./data/evidence_korea_addendum_10.json'")
sw.write_text(s,encoding='utf-8')

sm=ROOT/'sitemap.xml'; s=sm.read_text(encoding='utf-8')
url='https://jinwooson1988.github.io/tortoise-food-db-korea/plant/dill/'
if url not in s:
    entry=f'  <url><loc>{url}</loc></url>\n'
    s=s.replace('</urlset>',entry+'</urlset>')
sm.write_text(s,encoding='utf-8')

subprocess.run(['python','scripts/generate_static_pages.py'],cwd=ROOT,check=True)
for rel in ['plant/mallow/index.html','plant/sowthistle/index.html','plant/clover/index.html']:
    subprocess.run(['git','checkout','HEAD','--',rel],cwd=ROOT,check=True)

print('promoted dill; master',len(plants),'assessed',cov['plants_with_explainable_assessment'])
