#!/usr/bin/env python3
"""Join GBIF batch artifacts to existing catalog and literature leads.

Output is review-ready candidate rows, never feeding verdicts.
"""
import argparse
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
def norm(value):
    return re.sub(r"\s+", " ", (value or "").strip()).casefold()

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--batches", nargs="+", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    plants = json.loads((ROOT / "data/plants.json").read_text(encoding="utf-8"))
    known = {norm(p["scientific"]): p for p in plants if p.get("scientific")}
    lead_path = ROOT / "research/evidence_leads/global_direct_evidence_20261016_01.json"
    leads = json.loads(lead_path.read_text(encoding="utf-8"))["records"]
    existing_evidence = json.loads((ROOT / "data/public_evidence_records.json").read_text(encoding="utf-8"))["records"]
    by_plant_id = {}
    for evidence in existing_evidence:
        for pid in evidence.get("plant_ids", []):
            by_plant_id.setdefault(pid, []).append(evidence)
    mentions = {}
    for lead in leads:
        for taxon in lead.get("plant_taxa", []):
            if re.search(r"\bsp(?:p)?\.", taxon, re.I):
                continue
            mentions.setdefault(norm(taxon), []).append(lead)
    all_candidates = {}
    batches = []
    for path in args.batches:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload.get("candidates"), list):
            raise ValueError(f"Not a GBIF candidate batch: {path}")
        batches.append({"file":str(path),"candidates":len(payload["candidates"])})
        for c in payload["candidates"]:
            key = c.get("gbif_taxon_key")
            if not isinstance(key,int) or not c.get("scientific"):
                continue
            all_candidates[key] = c
    rows = []
    for key,c in sorted(all_candidates.items()):
        scientific = c["scientific"]
        existing = known.get(norm(scientific))
        sources = mentions.get(norm(scientific),[])
        linked_evidence = by_plant_id.get(existing["id"], []) if existing else []
        rows.append({"gbif_taxon_key":key,"scientific":scientific,
                     "family":c.get("family"),"gbif_url":c.get("source",{}).get("url"),
                     "existing_plant_id":existing["id"] if existing else None,
                     "existing_evidence_ids":[e["id"] for e in linked_evidence],
                     "existing_evidence_source_urls":[e.get("url") for e in linked_evidence],
                     "existing_evidence_linkage_scope":"catalog_plant_id_only_not_independent_taxon_verification" if linked_evidence else None,
                     "evidence_lead_ids":[s["id"] for s in sources],
                     "evidence_lead_urls":[s["url"] for s in sources],
                     "status":"literature_lead_requires_full_text_review" if sources else
                              "existing_catalog_match" if existing else "taxonomy_only",
                     "feeding_verdict":None,
                     "site_publishable":False})
    counts = Counter(r["status"] for r in rows)
    result = {"summary":{"batch_files":len(batches),"unique_gbif_candidates":len(rows),
                          "statuses":dict(counts),
                          "existing_evidence_links":sum(len(r["existing_evidence_ids"]) for r in rows),
                          "literature_lead_links":sum(len(r["evidence_lead_ids"]) for r in rows)},
              "warning":"Taxonomy is not feeding evidence. Full text, animal species and plant part must be verified before publication.",
              "batches":batches,"rows":rows}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result["summary"],ensure_ascii=False))
if __name__ == "__main__":
    main()
