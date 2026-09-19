#!/usr/bin/env python3
import json,pathlib,sys
p=pathlib.Path("data/reconciliation/curated69_wcvp.json")
if not p.exists():
 print("reconciliation output not committed yet; contract QA only");sys.exit(0)
rows=json.loads(p.read_text(encoding="utf-8")); errors=[]
for r in rows:
 if r["match_status"]=="genus_scope" and r.get("automatic_species_resolution") is not False: errors.append(r["plant_id"]+": genus scope was collapsed")
 if r.get("automatic_species_resolution") and r.get("match_status")!="exact_unique_accepted": errors.append(r["plant_id"]+": unsafe automatic resolution")
if errors: print("\n".join(errors));sys.exit(1)
print("curated-WCVP reconciliation QA OK:",len(rows))
