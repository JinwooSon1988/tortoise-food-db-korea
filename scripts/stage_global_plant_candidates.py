#!/usr/bin/env python3
"""Stage worldwide plant records without changing feeding assessments.

Input: JSON array of candidate records.
Output: normalized staging file. Promotion to global_plant_corpus.json is a separate reviewed step.
"""
import argparse, json, pathlib, re, unicodedata
from datetime import date

def clean(s):
    if s is None: return None
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", str(s))).strip()

def slug(s):
    s=clean(s).casefold()
    return re.sub(r"[^a-z0-9]+","-",s).strip("-")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("--output",default="data/staging/global_plant_candidates.normalized.json")
    args=ap.parse_args()
    rows=json.loads(pathlib.Path(args.input).read_text(encoding="utf-8"))
    out=[]; seen=set()
    for i,r in enumerate(rows):
        name=clean(r.get("canonical_scientific_name") or r.get("scientific_name"))
        source_id=clean(r.get("source_id"))
        source_url=clean(r.get("source_url"))
        if not name or not source_id or not source_url:
            raise SystemExit(f"row {i}: scientific name, source_id and source_url are required")
        source_record_id=clean(r.get("source_record_id"))
        candidate_id=clean(r.get("candidate_id")) or f"{slug(source_id)}:{source_record_id or slug(name)}"
        dedupe=(source_id.casefold(),(source_record_id or name).casefold())
        if dedupe in seen: continue
        seen.add(dedupe)
        out.append({
          "candidate_id":candidate_id,
          "canonical_scientific_name":name,
          "authorship":clean(r.get("authorship")),
          "family":clean(r.get("family")),
          "taxonomic_status":clean(r.get("taxonomic_status")) or "unresolved",
          "accepted_name":clean(r.get("accepted_name")),
          "source_id":source_id,
          "source_name":clean(r.get("source_name")) or source_id,
          "source_url":source_url,
          "source_record_id":source_record_id,
          "license":clean(r.get("license")),
          "observed_at":clean(r.get("observed_at")) or date.today().isoformat(),
          "reconciliation_status":"pending",
          "feed_review_status":"identity_only"
        })
    p=pathlib.Path(args.output); p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"staged {len(out)} normalized candidates -> {p}")

if __name__=="__main__": main()
