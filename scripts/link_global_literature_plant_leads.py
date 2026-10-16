#!/usr/bin/env python3
"""Match reviewed literature leads to existing plant IDs without genus-to-species overreach."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
plants = json.loads((ROOT / "data/plants.json").read_text(encoding="utf-8"))
leads = json.loads((ROOT / "research/evidence_leads/global_direct_evidence_20261016_01.json").read_text(encoding="utf-8"))["records"]
def norm(name):
    return re.sub(r"\\s+", " ", (name or "").strip().lower())
def genus(name):
    return norm(name).split(" ")[0]
def is_genus_scope(name):
    return bool(re.search(r"\\b(?:spp?\\.|sp\\.)", name, re.I))
out = []
for lead in leads:
    for taxon in lead.get("plant_taxa", []):
        exact = [p["id"] for p in plants if norm(p.get("scientific")) == norm(taxon)]
        same_genus = [p["id"] for p in plants if genus(p.get("scientific")) == genus(taxon)]
        if is_genus_scope(taxon):
            match = "genus_scope_only"
            # Existing genus-level names are matched at the same rank, not species level.
            matched = [p["id"] for p in plants if norm(p.get("scientific")) == norm(taxon)]
        elif exact:
            match = "exact_scientific_name"
            matched = exact
        elif same_genus:
            match = "same_genus_not_same_species"
            matched = []
        else:
            match = "missing_from_plant_catalog"
            matched = []
        out.append({"evidence_id": lead["id"], "source_url": lead["url"],
                    "animal_taxon": lead["animal_taxon"], "reported_plant_taxon": taxon,
                    "match_status": match, "eligible_plant_ids": matched,
                    "related_genus_ids_not_evidence": sorted(set(same_genus)-set(matched)),
                    "feeding_verdict": None, "publication_status": "review_required"})
result = {"warning": "Matching a plant name does not establish safe feeding or transfer across tortoise species.",
          "rows": out}
path = ROOT / "research/generated/global_literature_plant_match_queue.json"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\\n", encoding="utf-8")
print(json.dumps({"taxa":len(out),"exact_or_same_rank":sum(bool(r["eligible_plant_ids"]) for r in out),
                  "not_directly_matched":sum(not r["eligible_plant_ids"] for r in out)},ensure_ascii=False))
