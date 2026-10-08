#!/usr/bin/env python3
"""QA for the dry-matter composition registry and the worldwide research log.

Dry-matter (DM) records must keep the published unit/denominator, never carry per-100 g fresh fields,
exclude equation-derived values, and match the master taxon exactly. Every adopted finding in the research
log must exist in a registry, and nothing in the log may be adopted for a plant that is not a master plant.
"""
import json, re, sys
from pathlib import Path

R = Path(__file__).resolve().parents[1]
load = lambda rel: json.loads((R / rel).read_text(encoding="utf-8"))
plants = {p["id"]: p for p in load("data/plants.json")}
dm = load("data/plant_nutrition_dm_basis_v1.json")
log = load("data/nutrition_global_research_log_v1.json")
fresh = {r["plant_id"] for r in load("data/plant_nutrition_v56.json")["plants"] if r.get("verification_status") == "verified"}
errors = []

UNIT = {"dry_matter_pct_as_fed": None, "_pct_dm": None, "_g_per_kg_dm": None}
seen = set()
for r in dm["records"]:
    tag = f'{r.get("plant_id")}:{r.get("source_id")}'
    if tag in seen: errors.append(f"{tag}: duplicate record")
    seen.add(tag)
    if r.get("plant_id") not in plants: errors.append(f"{tag}: unknown plant")
    elif r.get("scientific_name") != plants[r["plant_id"]]["scientific"]: errors.append(f"{tag}: scientific_name differs from master")
    for k in ("source_name", "source_id", "source_url", "variant", "plant_part", "preparation_state", "basis", "verified_at", "source_scientific_name"):
        if not r.get(k): errors.append(f"{tag}: missing {k}")
    if not str(r.get("source_url", "")).startswith("https://"): errors.append(f"{tag}: source_url must be https")
    if "dry matter" not in str(r.get("basis", "")).lower(): errors.append(f"{tag}: basis must state dry matter")
    if r.get("preparation_state") not in {"fresh", "hay"}: errors.append(f"{tag}: unexpected preparation_state")
    # master taxon must equal the source species (binomial), never a congener
    src = re.sub(r"\s+", " ", r.get("source_scientific_name", "")).split()[:2]
    mst = re.sub(r"\s+", " ", r.get("scientific_name", "")).split()[:2]
    if [s.lower() for s in src] != [m.lower() for m in mst]: errors.append(f"{tag}: source species {src} != master {mst}")
    for k, v in r.get("values", {}).items():
        if not (k == "dry_matter_pct_as_fed" or k.endswith("_pct_dm") or k.endswith("_g_per_kg_dm")): errors.append(f"{tag}: unexpected value key {k}")
        if k in r.get("excluded_equation_values", []): errors.append(f"{tag}: equation-derived value {k} stored")
        if not isinstance(v.get("value"), (int, float)) or v["value"] < 0: errors.append(f"{tag}: {k} must be a non-negative number")
    if any(re.search(r"_(g|mg|ug)$", k) for k in r): errors.append(f"{tag}: per-100 g fresh field present in DM record")
    ca, p, ratio = r["values"].get("calcium_g_per_kg_dm"), r["values"].get("phosphorus_g_per_kg_dm"), r.get("calcium_phosphorus_ratio")
    if ratio is not None and (not ca or not p or abs(ca["value"] / p["value"] - ratio) > 0.02): errors.append(f"{tag}: Ca:P inconsistent")

dm_sources = {r["source_id"] for r in dm["records"]}
for s in log["sources"]:
    for f in s.get("findings", []):
        if f["decision"] not in {"adopted", "rejected", "held"}: errors.append(f'{s["id"]}: bad decision {f["decision"]}')
        if not f.get("reason"): errors.append(f'{s["id"]}:{f["plant_id"]}: reason required')
        if f["plant_id"] not in plants: errors.append(f'{s["id"]}: unknown plant {f["plant_id"]}')
        if f["decision"] == "adopted" and f["plant_id"] not in fresh and not any(f["record"].startswith(x) for x in dm_sources):
            errors.append(f'{s["id"]}:{f["plant_id"]}: adopted but not present in any registry')

if errors:
    for e in errors: print("ERROR:", e)
    sys.exit(f"DM registry / research log QA FAILED: {len(errors)} error(s)")
print(f"OK: {len(dm['records'])} DM-basis records for {len({r['plant_id'] for r in dm['records']})} plants; research log {len(log['sources'])} sources consistent")
