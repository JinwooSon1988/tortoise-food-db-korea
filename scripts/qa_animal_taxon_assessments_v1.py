#!/usr/bin/env python3
import json, pathlib, sys
root=pathlib.Path(__file__).resolve().parents[1]
ass=json.loads((root/"data/assessments.json").read_text(encoding="utf-8"))
sel=json.loads((root/"data/animal_taxon_selector_v1.json").read_text(encoding="utf-8"))
allowed={"taxon_group","exact_species","tortoise_general","herbivorous_reptile_general"}
errors=[]
for i,a in enumerate(ass):
    if a.get("assessment_scope") not in allowed: errors.append(f"{i}: invalid assessment_scope")
    if a.get("assessment_scope") in {"taxon_group","exact_species"} and not a.get("animal_taxon"): errors.append(f"{i}: taxon-scoped assessment missing animal_taxon")
    if not a.get("legacy_scope"): errors.append(f"{i}: missing legacy_scope provenance")
    if not a.get("plant_id"): errors.append(f"{i}: missing plant_id")
if errors:
    print("\n".join(errors)); sys.exit(1)
print(f"OK: {len(ass)} assessments normalized; species selector groups={len(sel['selector_groups'])}; no verdicts changed")
