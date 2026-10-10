#!/usr/bin/env python3
"""Read-only integrity QA for nutrition reference sidecar. Does not edit site/UI or verdicts."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))

plants = read("data/plants.json")
assessments = read("data/public_assessments.json")
references = read("data/plant_nutrition_reference_v1.json")["records"]
official = read("data/plant_nutrition_v56.json")["plants"]
rda = read("data/rda_food_composition_v56.json")["records"]
plant_ids = {p["id"] for p in plants}
published = {a["plant_id"] for a in assessments}
verified = {r["plant_id"] for r in official if r.get("verification_status") == "verified"}
verified.update(r["plant_id"] for r in rda if r.get("identity_match") == "exact" and r.get("values_per_100g"))
issues = []
by_plant = {}
seen_ids = set()
for r in references:
    rid = r.get("reference_id")
    pid = r.get("plant_id")
    if not rid or rid in seen_ids:
        issues.append(f"missing/duplicate reference_id: {rid}")
    seen_ids.add(rid)
    if pid not in plant_ids:
        issues.append(f"{rid}: unknown plant_id {pid}")
    for field in ("source_name", "source_url", "analyzed_part", "preparation_state", "basis", "display_note_ko"):
        if not r.get(field):
            issues.append(f"{rid}: missing {field}")
    if r.get("status") != "reference_only":
        issues.append(f"{rid}: unexpected status")
    if not r.get("nutrients"):
        issues.append(f"{rid}: no numeric nutrients")
    if r.get("feeding_verdict_use") is not False or r.get("primary_eligible") is not False:
        issues.append(f"{rid}: must not promote reference to verified or verdict")
    if r.get("display_tier") not in {"related_part_reference", "dry_matter_reference", "related_species_reference", "related_cultivar_reference"}:
        issues.append(f"{rid}: unknown display tier")
    if r.get("display_tier") == "dry_matter_reference" and not any(token in r.get("basis", "").lower() for token in ("dry", "dm", "건물", "건조")):
        issues.append(f"{rid}: dry matter tier lacks dry basis")
    if r.get("source_url") and not r["source_url"].startswith("https://"):\n        issues.append(f"{rid}: source URL must use HTTPS")\n    for name, value in r.get("nutrients", {}).items():
        if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
            issues.append(f"{rid}: invalid numeric value for {name}")
    by_plant.setdefault(pid, []).append(r)

public_plants = published & plant_ids
official_ids = public_plants & verified
reference_only = {pid for pid in public_plants if pid not in verified and pid in by_plant}
unlinked = public_plants - official_ids - reference_only
if len(official_ids) + len(reference_only) + len(unlinked) != len(public_plants):
    issues.append("published coverage tiers fail partition")
if official_ids & reference_only or official_ids & unlinked or reference_only & unlinked:
    issues.append("published coverage tiers overlap")

print(f"Published {len(public_plants)}: official {len(official_ids)}, reference-only {len(reference_only)}, unlinked {len(unlinked)}")
print(f"Reference records {len(references)} across {len(by_plant)} plant IDs")
if issues:
    for issue in issues:
        print("FAIL:", issue)
    raise SystemExit(1)
print("PASS: reference metadata and exclusive coverage tiers; original-source numeric verification NOT performed")
