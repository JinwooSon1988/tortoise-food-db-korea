#!/usr/bin/env python3
import json, pathlib, sys
P=pathlib.Path(__file__).resolve().parents[1]
rows=json.loads((P/"data/global_plant_corpus.json").read_text(encoding="utf-8"))
errors=[]; ids=set(); names={}
allowed={"identity_only","evidence_found","assessed","unresolved"}
for i,r in enumerate(rows):
    rid=r.get("record_id"); name=(r.get("canonical_scientific_name") or "").strip()
    if not rid or rid in ids: errors.append(f"{i}: missing/duplicate record_id {rid!r}")
    ids.add(rid)
    if not name: errors.append(f"{rid}: canonical_scientific_name required")
    key=name.casefold()
    if key in names and r.get("taxonomic_status")=="accepted" and names[key]=="accepted": errors.append(f"{rid}: duplicate accepted canonical name {name}")
    names[key]=r.get("taxonomic_status")
    if not r.get("family"): errors.append(f"{rid}: family required")
    if r.get("feed_review_status") not in allowed: errors.append(f"{rid}: invalid feed_review_status")
    prov=r.get("provenance") or []
    if not prov: errors.append(f"{rid}: provenance required")
    for p in prov:
        for k in ("source_id","source_name","source_url","observed_at"):
            if not p.get(k): errors.append(f"{rid}: provenance.{k} required")
    if r.get("feed_review_status")=="identity_only" and r.get("feed_assessment") is not None:
        errors.append(f"{rid}: identity_only must not contain feed_assessment")
    if r.get("taxonomic_status")=="synonym" and not r.get("accepted_record_id"):
        errors.append(f"{rid}: synonym requires accepted_record_id; never silently collapse synonyms")
if errors:
    print("\n".join(errors)); sys.exit(1)
print(f"global plant corpus QA OK: {len(rows)} records")
