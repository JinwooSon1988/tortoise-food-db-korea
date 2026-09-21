#!/usr/bin/env python3
import json, re, sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
plants={x["id"]:x for x in json.loads((R/"data/plants.json").read_text(encoding="utf-8"))}
rows=json.loads((R/"data/verified_plant_images_v56.json").read_text(encoding="utf-8")).get("images",[])
errors=[]
seen=set()
allowed={"exact_species","exact_subspecies","exact_variety"}
for x in rows:
    pid=x.get("plant_id")
    if pid in seen: errors.append(f"duplicate plant_id: {pid}")
    seen.add(pid)
    if pid not in plants: errors.append(f"unknown plant_id: {pid}")
    for k in ("scientific","image_url","source_url","creator","license","license_url","identity_scope","master_scientific","verified_at"):
        if not x.get(k): errors.append(f"{pid}: missing {k}")
    if x.get("identity_scope") not in allowed: errors.append(f"{pid}: invalid identity_scope {x.get('identity_scope')}")
    if not str(x.get("source_url","")).startswith("https://commons.wikimedia.org/wiki/File:"): errors.append(f"{pid}: non-Commons source_url")
    if not str(x.get("image_url","")).startswith("https://commons.wikimedia.org/wiki/Special:Redirect/file/"): errors.append(f"{pid}: unexpected image_url")
    master=plants.get(pid,{}).get("scientific","")
    if re.search(r"\bspp\.", master, re.I): errors.append(f"{pid}: spp.-level master cannot receive one species representative image")
    if x.get("master_scientific") != master: errors.append(f"{pid}: master_scientific mismatch")
    if x.get("scientific") != master: errors.append(f"{pid}: image scientific scope does not exactly match master")
if errors:
    print("\n".join(errors)); sys.exit(1)
print(f"PASS: {len(rows)} verified images; unique IDs, exact master taxon scope, Commons provenance, license metadata.")
