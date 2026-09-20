import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
registry=json.loads((ROOT/'data/verified_plant_images_v56.json').read_text(encoding='utf-8'))
plants=json.loads((ROOT/'data/plants.json').read_text(encoding='utf-8'))
master={p['id']:p for p in plants}
required=set(registry['policy']['required_fields'])
seen=set()
for image in registry['images']:
    pid=image['plant_id']
    assert required <= set(image),(pid,required-set(image))
    assert pid in master and pid not in seen,pid
    seen.add(pid)
    assert 'spp.' not in master[pid]['scientific'],f'{pid}: genus-level master must keep placeholder'
    assert image['scientific']==master[pid]['scientific'],(pid,image['scientific'],master[pid]['scientific'])
    assert image['identity_scope'] in {'exact_species','exact_subspecies','exact_variety'},pid
    assert image['source_url'].startswith('https://commons.wikimedia.org/wiki/File:'),pid
    assert image['license_url'].startswith('https://creativecommons.org/'),pid
for item in registry.get('rejected_candidates',[]):
    assert item['plant_id'] in master
    assert item['master_scientific']==master[item['plant_id']]['scientific']
print(f"verified image registry OK: {len(seen)} accepted, {len(registry.get('rejected_candidates',[]))} rejected")
