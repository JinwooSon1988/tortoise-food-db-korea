#!/usr/bin/env python3
"""QA for the worldwide source registry, FAO/INFOODS directory survey and unverified observation lane.

Enforces docs/COMMUNITY_EVIDENCE_SEPARATION_POLICY_2026-10-08.md: observations stay in their own lane, carry the
minimum schema with explicit 'unknown' values, store no user identifiers / text copies / coordinates, and never
feed grades, nutrient values or safe amounts. Blocked or restricted sources must state the required user action.
"""
import json, re, sys
from pathlib import Path

R = Path(__file__).resolve().parents[1]
load = lambda rel: json.loads((R / rel).read_text(encoding="utf-8"))
plants = {p["id"] for p in load("data/plants.json")}
errors = []

# ---- source registry
reg = load("data/global_source_registry_v1.json")
lanes = set(reg["lanes"])
ids = set()
for s in reg["sources"]:
    tag = s.get("id")
    if tag in ids: errors.append(f"registry: duplicate id {tag}")
    ids.add(tag)
    if s.get("evidence_lane") not in lanes: errors.append(f"registry {tag}: unknown lane")
    for k in ("name", "url", "access_status", "reuse_permission", "result_in_this_project", "checked_at"):
        if not s.get(k): errors.append(f"registry {tag}: missing {k}")
    if not str(s.get("url", "")).startswith("https://"): errors.append(f"registry {tag}: url must be https")
    blocked = re.search(r"blocked|requires|required|subscription|registration|print-only|disallow", s.get("access_status", ""), re.I)
    if blocked and not s.get("user_action_required"): errors.append(f"registry {tag}: blocked/restricted source needs user_action_required")
    if re.search(r"password|token=|api_key|secret", json.dumps(s), re.I): errors.append(f"registry {tag}: credential-like content")
if len(reg["sources"]) < 20: errors.append("registry: fewer than 20 sources")

# ---- FAO/INFOODS directory survey
fao = load("data/fao_infoods_directory_access_v1.json")
urls = [e["fao_directory_url"] for e in fao["entries"]]
if len(urls) != len(set(urls)): errors.append("fao: duplicate entries")
if fao["summary"]["entries"] != len(fao["entries"]): errors.append("fao: summary count mismatch")
for e in fao["entries"]:
    if not e.get("access_as_listed_by_fao"): errors.append(f'fao {e["fao_directory_url"]}: access missing (use "unknown")')

# ---- unverified observations
obs = load("data/unverified_observations_v1.json")
REQUIRED = ("source_url", "platform", "observed_or_posted_at", "retrieved_at", "observation_type", "animal_taxon_original", "plant_items",
            "plant_part", "preparation_state", "reported_exposure", "reported_outcome", "duration", "number_of_animals", "husbandry_context",
            "limitations", "contradictory_reports", "independent_validation", "copyright_access_status", "editorial_status", "license")
FORBIDDEN_KEYS = {"user", "user_login", "username", "user_name", "observer", "profile", "photos", "photo_url", "description", "body", "text",
                  "latitude", "longitude", "location", "geojson", "email"}
seen = set()
for r in obs["records"]:
    tag = r.get("id")
    if tag in seen: errors.append(f"obs: duplicate {tag}")
    seen.add(tag)
    if r.get("lane") != "unverified_observation": errors.append(f"obs {tag}: wrong lane")
    for k in REQUIRED:
        if k not in r or r[k] in (None, ""): errors.append(f"obs {tag}: {k} must be present (use 'unknown')")
    for k in r:
        if k.lower() in FORBIDDEN_KEYS: errors.append(f"obs {tag}: forbidden personal/content field {k}")
    if r.get("independent_validation") not in {"unverified", "partial", "independently_supported", "contradicted"}: errors.append(f"obs {tag}: bad independent_validation")
    if r.get("editorial_status") not in {"lead", "reviewed", "excluded", "eligible_for_reference"}: errors.append(f"obs {tag}: bad editorial_status")
    if r.get("observation_type") not in {"firsthand", "secondhand", "advice_only", "unknown"}: errors.append(f"obs {tag}: bad observation_type")
    for it in r.get("plant_items", []):
        if it.get("master_plant_id") and it["master_plant_id"] not in plants: errors.append(f"obs {tag}: unknown master plant {it['master_plant_id']}")
        if it.get("master_match") not in {"exact_species", "genus_observation_to_genus_master", "none", "not_a_plant"}: errors.append(f"obs {tag}: bad master_match")
    if any(re.search(r"_(g|mg|ug)$|verdict|grade_|safe_amount", k) for k in r): errors.append(f"obs {tag}: nutrient/verdict field not allowed in observation lane")
    if r.get("independent_validation") == "partial":
        if not all(it.get("linked_quality_grade") == "research" for it in r["plant_items"] if it.get("kingdom_hint") == "Plantae"):
            errors.append(f"obs {tag}: partial requires research-grade plant identification")

# ---- no lane leakage into published verdict / nutrition data
pa = json.dumps(load("data/public_assessments.json"), ensure_ascii=False)
nut = json.dumps(load("data/plant_nutrition_v56.json"), ensure_ascii=False)
for marker in ("inaturalist.org", "tortoiseforum.org", "reddit.com", "dcinside.com", "cafe.naver.com"):
    if marker in pa or marker in nut: errors.append(f"community/citizen source {marker} leaked into verdict or nutrition data")

if errors:
    for e in errors: print("ERROR:", e)
    sys.exit(f"global source QA FAILED: {len(errors)} error(s)")
print(f"OK: registry {len(reg['sources'])} sources, FAO directory {len(fao['entries'])} entries, {len(obs['records'])} unverified observations; lanes separated")
