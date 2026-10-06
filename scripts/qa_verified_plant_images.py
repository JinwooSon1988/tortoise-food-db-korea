#!/usr/bin/env python3
import json, sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/"scripts"))
from plant_taxon_scope import ACCEPTED_SCOPES, check_image, required_scope
plants={x["id"]:x for x in json.loads((R/"data/plants.json").read_text(encoding="utf-8"))}
registry=json.loads((R/"data/verified_plant_images_v56.json").read_text(encoding="utf-8"))
rows=registry.get("images",[])
required=registry.get("policy",{}).get("required_fields",[])
errors=[]
seen=set()
for x in rows:
    pid=x.get("plant_id")
    if pid in seen: errors.append(f"duplicate plant_id: {pid}")
    seen.add(pid)
    if pid not in plants:
        errors.append(f"unknown plant_id: {pid}"); continue
    for k in required:
        if not x.get(k): errors.append(f"{pid}: missing {k}")
    if x.get("identity_scope") not in ACCEPTED_SCOPES: errors.append(f"{pid}: invalid identity_scope {x.get('identity_scope')}")
    if not str(x.get("source_url","")).startswith("https://commons.wikimedia.org/wiki/File:"): errors.append(f"{pid}: non-Commons source_url")
    if not str(x.get("image_url","")).startswith("https://commons.wikimedia.org/wiki/Special:Redirect/file/"): errors.append(f"{pid}: unexpected image_url")
    if not str(x.get("license_url","")).startswith("https://creativecommons.org/"): errors.append(f"{pid}: license_url must be a creativecommons.org URL")
    if x.get("part_match") not in registry.get("policy",{}).get("part_match_values",{}): errors.append(f"{pid}: invalid part_match {x.get('part_match')}")
    errors += [f"{pid}: {p}" for p in check_image(x, plants[pid].get("scientific",""))]
for item in registry.get("rejected_candidates",[]):
    pid=item.get("plant_id")
    if pid not in plants: errors.append(f"rejected candidate unknown plant_id: {pid}"); continue
    if item.get("master_scientific")!=plants[pid].get("scientific"): errors.append(f"rejected {pid}: master_scientific mismatch")
    if pid in seen and required_scope(plants[pid].get("scientific","")) is None: errors.append(f"{pid}: unresolved master has an accepted image")
if errors:
    print("\n".join(errors)); sys.exit(1)
print(f"PASS: {len(rows)} verified images; unique IDs, master-rank identity scope, no spp./agg. representatives, Commons provenance, license metadata.")
