from pathlib import Path
import json, sys

ROOT=Path(__file__).resolve().parents[1]
registry=json.loads((ROOT/"data/animal_taxa_v1.json").read_text(encoding="utf-8"))
taxa=registry["taxa"]
ids=[x["id"] for x in taxa]
errors=[]
if len(ids)!=len(set(ids)): errors.append("duplicate taxon id")
for x in taxa:
    for k in ("id","scientific","ko","en","scope"):
        if not x.get(k): errors.append(f"{x.get('id','?')}: missing {k}")
    if x.get("scope") not in {"species","genus_group"}:
        errors.append(f"{x['id']}: invalid scope")
# Future multi-taxon assessments are optional during migration, but if present they must be canonical.
path=ROOT/"data/assessments_by_taxon_v1.json"
if path.exists():
    rows=json.loads(path.read_text(encoding="utf-8"))
    valid=set(ids)
    seen=set()
    for r in rows:
        key=(r.get("plant_id"),r.get("taxon_id"))
        if not all(key): errors.append("assessment missing plant_id/taxon_id"); continue
        if r["taxon_id"] not in valid: errors.append(f"{key}: unknown taxon_id")
        if key in seen: errors.append(f"{key}: duplicate assessment")
        seen.add(key)
        if not r.get("evidence_ids"): errors.append(f"{key}: no evidence_ids")
        if not r.get("verdict"): errors.append(f"{key}: no verdict")
        if not r.get("applicability_note"): errors.append(f"{key}: applicability_note missing")
        if not r.get("applicability_note_en"): errors.append(f"{key}: applicability_note_en missing")
if errors:
    print("FAIL: animal taxon registry / assessment contract")
    for e in errors: print("-",e)
    sys.exit(1)
print(f"PASS: {len(taxa)} canonical tortoise taxa; multi-taxon assessment contract valid")
