#!/usr/bin/env python3
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from plant_taxon_scope import required_scope
plants=json.loads((ROOT/"data/plants.json").read_text(encoding="utf-8"))
images=json.loads((ROOT/"data/verified_plant_images_v56.json").read_text(encoding="utf-8")).get("images",[])
have={x["plant_id"] for x in images}
missing=[p for p in plants if p["id"] not in have]
def bucket(sc):
    scope=required_scope(sc)
    if scope is None: return "genus_scope_hold"
    if scope in ("exact_subspecies","exact_variety"): return "exact_infraspecific_candidate"
    return "exact_species_candidate"
groups={k:[] for k in ("exact_species_candidate","exact_infraspecific_candidate","genus_scope_hold")}
for p in missing: groups[bucket(p.get("scientific",""))].append({"plant_id":p["id"],"scientific":p.get("scientific"),"ko":p.get("ko"),"required_scope":required_scope(p.get("scientific",""))})
out={"schema_version":2,"policy":"An image may represent a master record only at the master's own rank (species, subspecies or variety). spp./agg./s.l. masters never receive a species representative image. Exact taxon and license provenance are required before publication.","counts":{k:len(v) for k,v in groups.items()},"groups":groups}
(ROOT/"data/image_gap_triage_v1.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(out["counts"],ensure_ascii=False))
