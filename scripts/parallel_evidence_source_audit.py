#!/usr/bin/env python3
"""Parallel audit of evidence-first leads, plus wild-record quarantine.

Outputs source-type triage and exact unresolved taxa. Does not assert feeding
safety, extrapolate husbandry frequency, or auto-promote feeding_pending.
"""
import argparse,concurrent.futures,json,re
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_text(encoding="utf-8"))
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--workers",type=int,default=20)
    args=ap.parse_args()
    if not 1<=args.workers<=32:ap.error("workers must be 1..32")
    manifest=load("data/evidence-first-queue/index.json")
    jobs=[(s["file"],load("data/evidence-first-queue/"+s["file"])["records"]) for s in manifest["shards"]]
    wild=load("data/wild_feeding_evidence.json")["records"]
    by_name={r["plant_taxon_reported"].lower():r for r in wild}
    by_id={r["plant_id"]:r for r in wild}
    def inspect(row):
        mentions=row["mentions"]
        source_types=sorted(set(str(m.get("source_type") or "") for m in mentions))
        taxonomy_only=all(t in ("taxonomy_database","peer_reviewed_plant_composition") for t in source_types)
        pid=row.get("reviewed_plant_id")
        w=by_id.get(pid) if pid else by_name.get(row["scientific_name"].lower())
        wild_review=None
        if w:
            exact=w["plant_taxon_reported"].lower()==row["scientific_name"].lower()
            accepted=w["plant_taxon_accepted"].split(" ")[:2]
            alias=not exact and " ".join(accepted).lower()!=row["scientific_name"].lower()
            wild_review={"record_id":w["id"],"source_id":w["source_id"],"tortoise_taxon":w["tortoise_taxon"],
                "plant_taxon_reported":w["plant_taxon_reported"],"plant_taxon_accepted":w["plant_taxon_accepted"],
                "plant_part":w.get("plant_part"),"study_method":w.get("study_method"),
                "season":w.get("season"),"feeding_signal":w.get("feeding_signal"),
                "limitations":w.get("limitations"),
                "taxon_match_status":"requires_synonym_review" if alias else "binomial_match",
                "feeding_frequency":"not_reported_as_husbandry_schedule",
                "feeding_amount":"not_reported_as_husbandry_quantity",
                "mixed_with":"not_reported","cutting_method":"not_reported",
                "safety_grade":None}
        return {"scientific_name":row["scientific_name"],"reviewed_plant_id":pid,
            "candidate_taxon_id":row.get("candidate_taxon_id"),
            "identity_status":row["identity_status"],
            "reference_types":source_types,"reference_count":len(mentions),
            "taxonomy_or_composition_only":taxonomy_only,
            "wild_record_for_manual_review":wild_review,
            "feeding_pending_approved":False,"safety_grade":None}
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        result=list(pool.map(inspect,(row for _,batch in jobs for row in batch)))
    counts=Counter()
    for r in result:
        counts["reviewed_leads"]+=1
        counts["identity_check_needed"]+=r["identity_status"]=="identity_check_needed"
        counts["taxonomy_or_composition_only"]+=r["taxonomy_or_composition_only"]
        counts["wild_record_requires_review"]+=bool(r["wild_record_for_manual_review"])
        counts["synonym_review_required"]+=bool(r["wild_record_for_manual_review"] and r["wild_record_for_manual_review"]["taxon_match_status"]=="requires_synonym_review")
    if len(result)!=manifest["counts"]["unique_taxa_mentioned"]:raise SystemExit("review queue count mismatch")
    out={"schema_version":"1.0","scope":"manual source audit; no feeding or safety approval",
         "counts":dict(counts),"records":result}
    dest=ROOT/"data/evidence-first-source-audit.json"
    dest.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(counts,ensure_ascii=False))
if __name__=="__main__":main()
