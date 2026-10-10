import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from plant_taxon_scope import check_image
registry=json.loads((ROOT/'data/verified_plant_images_v56.json').read_text(encoding='utf-8'))
plants=json.loads((ROOT/'data/plants.json').read_text(encoding='utf-8'))
master={p['id']:p for p in plants}
required=set(registry['policy']['required_fields'])
PD_TEMPLATES={'https://commons.wikimedia.org/wiki/Template:PD-USGov-NPS','https://commons.wikimedia.org/wiki/Template:PD-self'}
seen=set()
for image in registry['images']:
    pid=image['plant_id']
    assert required <= set(image),(pid,required-set(image))
    assert pid in master and pid not in seen,pid
    seen.add(pid)
    problems=check_image(image,master[pid]['scientific'])
    assert not problems,(pid,problems)
    assert image['source_url'].startswith('https://commons.wikimedia.org/wiki/File:'),pid
    # Same licence rule as scripts/qa_verified_plant_images.py: Creative Commons, or an explicitly documented
    # Wikimedia Commons public-domain template for a record whose licence is 'Public domain ...'.
    assert image['license_url'].startswith('https://creativecommons.org/') or (str(image.get('license','')).startswith('Public domain') and image['license_url'] in PD_TEMPLATES),pid
for item in registry.get('rejected_candidates',[]):
    assert item['plant_id'] in master
    assert item['master_scientific']==master[item['plant_id']]['scientific']
print(f"verified image registry OK: {len(seen)} accepted, {len(registry.get('rejected_candidates',[]))} rejected")
