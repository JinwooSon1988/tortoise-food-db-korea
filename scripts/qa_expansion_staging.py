from pathlib import Path
import json,sys,re
ROOT=Path(__file__).resolve().parents[1]
d=json.loads((ROOT/"data/plant_expansion_staging.json").read_text(encoding="utf-8"))
risk=json.loads((ROOT/"data/wild_candidate_risk_screening.json").read_text(encoding="utf-8"))
risk_by_id={r.get("plant_id"):r for r in risk.get("records",[])}
allowed=set(d.get("stages",[])); errors=[]
for c in d.get("candidates",[]):
    cid=c.get("id","<missing>")
    stage=c.get("stage")
    if stage not in allowed: errors.append(f"{cid}: unknown stage {stage}")
    if c.get("public") and stage!="promoted": errors.append(f"{cid}: public before promoted")
    if stage in {"collected","taxonomy_verified","needs_species_resolution"} and c.get("feeding_grade") is not None:
        errors.append(f"{cid}: feeding grade assigned before evidence/assessment")
    genus_level=bool(re.search(r"\\bspp?\\.\\s*$",str(c.get("submitted_name","")),re.I))
    if genus_level and stage in {"assessed","promoted"}: errors.append(f"{cid}: genus-level candidate assessed/promoted")
    if stage=="needs_species_resolution" and not genus_level: errors.append(f"{cid}: species-resolution quarantine without genus-level submitted name")
    rr=risk_by_id.get(cid)
    if stage in {"evidence_researched","assessed","promoted"} and not rr:
        errors.append(f"{cid}: {stage} without risk-screening audit")
    if rr and stage in {"assessed","promoted"}:
        rstatus=str(rr.get("status",""))
        blocker=str(rr.get("publication_blocker") or "").strip()
        if rstatus.startswith("blocked") or rstatus=="research_gap":
            errors.append(f"{cid}: {stage} despite risk status {rstatus}")
        if blocker:
            errors.append(f"{cid}: {stage} while publication_blocker remains")
    if stage in {"taxonomy_verified","evidence_researched","assessed","promoted"}:
        for k in ("accepted_name","taxonomy_authority","taxonomy_checked"):
            if not c.get(k): errors.append(f"{cid}: {stage} missing {k}")
        if c.get("submitted_name_status")=="synonym" and c.get("accepted_name")==c.get("submitted_name"):
            errors.append(f"{cid}: synonym does not preserve distinct accepted name")
if "needs_species_resolution" not in allowed: errors.append("needs_species_resolution missing from allowed stages")
if errors:
    print("FAIL: expansion staging QA")
    for e in errors: print("-",e)
    sys.exit(1)
print(f"PASS: expansion staging QA ({len(d.get('candidates',[]))} candidates)")
