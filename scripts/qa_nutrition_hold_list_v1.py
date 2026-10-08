#!/usr/bin/env python3
"""QA: every public plant is either a verified nutrition record or an explicit hold entry, never both, and held
entries carry no nutrient values. New-style records must carry full provenance."""
import json, re, sys
from pathlib import Path

R = Path(__file__).resolve().parents[1]
load = lambda rel: json.loads((R / rel).read_text(encoding="utf-8"))
plants = {p["id"]: p for p in load("data/plants.json")}
nut = load("data/plant_nutrition_v56.json")
hold = load("data/nutrition_hold_list_v1.json")
errors = []

verified = {r["plant_id"]: r for r in nut["plants"] if r.get("verification_status") == "verified"}
held = {}
for h in hold["records"]:
    pid = h["plant_id"]
    if pid in held: errors.append(f"{pid}: duplicate hold entry")
    held[pid] = h
    if pid not in plants: errors.append(f"{pid}: hold entry for unknown plant")
    if h.get("hold_reason_code") not in hold["reason_codes"]: errors.append(f"{pid}: unknown hold_reason_code")
    if h.get("do_not_infer") is not True: errors.append(f"{pid}: do_not_infer must be true")
    if any(re.search(r"_(g|mg|ug|kcal)$|ratio", k) for k in h): errors.append(f"{pid}: hold entry must not carry nutrient values")
    for c in h.get("candidates_examined", []):
        if not (c.get("source_id") and c.get("rejected_because")): errors.append(f"{pid}: candidate needs source_id and rejected_because")
both = set(verified) & set(held)
if both: errors.append(f"plants both verified and held: {sorted(both)}")
missing = set(plants) - set(verified) - set(held)
if missing: errors.append(f"plants neither verified nor held: {sorted(missing)}")
if hold.get("held_count") != len(held): errors.append("held_count does not match records")

PROVENANCE = ("scientific_name", "source_institution", "source_kind", "source_id", "source_url", "dataset_release", "verified_at",
              "basis", "units", "plant_part", "preparation_state")
for pid, r in verified.items():
    if r.get("verified_at", "") >= "2026-10-08":  # records added or re-verified by the 2026-10 nutrition expansion
        for k in PROVENANCE + ("identity_match_basis", "applicability_note_ko"):
            if r.get(k) in (None, "", {}): errors.append(f"{pid}: missing provenance field {k}")
    if r.get("preparation_state") not in (None, "raw"): errors.append(f"{pid}: primary record must be raw")
    if r.get("scientific_name") and r["scientific_name"] != plants[pid]["scientific"]: errors.append(f"{pid}: scientific_name differs from master")
    for k in r.get("units", {}):
        if r.get(k) is None: errors.append(f"{pid}: unit declared for absent field {k}")

if errors:
    for e in errors: print("ERROR:", e)
    sys.exit(f"nutrition hold-list QA FAILED: {len(errors)} error(s)")
print(f"OK: {len(verified)} verified + {len(held)} held = {len(plants)} public plants; no overlap, no values in hold entries")
