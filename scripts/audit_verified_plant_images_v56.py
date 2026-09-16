import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
registry = json.loads((ROOT / 'data/verified_plant_images_v56.json').read_text(encoding='utf-8'))
plants = json.loads((ROOT / 'data/plants.json').read_text(encoding='utf-8'))
by_id = {p['id']: p for p in plants}
required = set(registry['policy']['required_fields'])
seen = set()

for item in registry['images']:
    missing = required - set(item)
    assert not missing, f"{item.get('plant_id')}: missing {sorted(missing)}"
    pid = item['plant_id']
    assert pid in by_id, f"unknown plant_id: {pid}"
    assert pid not in seen, f"duplicate image record: {pid}"
    seen.add(pid)
    master = by_id[pid]['scientific']
    assert 'spp.' not in master, f"{pid}: genus-level master must keep placeholder"
    assert item['scientific'] == master, f"{pid}: image taxon {item['scientific']} != master {master}"
    assert item['identity_scope'] == 'exact_species', f"{pid}: identity scope must be exact_species"
    assert item['source_url'].startswith('https://commons.wikimedia.org/wiki/File:'), f"{pid}: source must be a Commons file page"
    assert item['license_url'].startswith('https://creativecommons.org/'), f"{pid}: license URL missing"

for item in registry.get('rejected_candidates', []):
    assert item['plant_id'] in by_id
    assert item['master_scientific'] == by_id[item['plant_id']]['scientific']

print(f"verified image registry OK: {len(registry['images'])} accepted, {len(registry.get('rejected_candidates', []))} rejected")
