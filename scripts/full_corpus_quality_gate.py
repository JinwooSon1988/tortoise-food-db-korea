#!/usr/bin/env python3
"""Offline full-corpus QA gate; no unverified record can become a feeding grade.

Parallel shard validation + evidence review. Outputs a report only.
Run: python scripts/full_corpus_quality_gate.py --workers 20
"""
import argparse,concurrent.futures,hashlib,json,re,sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads((ROOT/p).read_text(encoding="utf-8"))
def digest(p, parsed):
    raw=p.read_bytes()
    variants=[raw, raw.replace(bytes([13,10]),bytes([10]))]
    # Match the shard builder's compact UTF-8 JSON with one LF.
    canonical=json.dumps(parsed,ensure_ascii=False,separators=(",",":")).encode("utf-8")
    variants.extend([canonical,canonical+bytes([10])])
    return {hashlib.sha256(v).hexdigest() for v in variants}
def inspect(job):
    prefix,shard=job
    path=ROOT/prefix/shard["file"]
    raw=read(str(path.relative_to(ROOT)))
    rows=raw.get("records",[])
    errors=[]
    if len(rows)!=shard["count"]:errors.append("count mismatch")
    if shard.get("sha256") and shard["sha256"] not in digest(path,raw):errors.append("sha256 mismatch (raw and deterministic JSON representations)")
    ids=set()
    for i,row in enumerate(rows):
        name=str(row.get("scientific_name") or "").strip()
        if not name or not re.match(r"^[A-Z][a-z-]+ [a-z][a-z-]+",name):
            errors.append("invalid scientific name row "+str(i))
        key=(row.get("taxon_id") or name).casefold()
        if key in ids:errors.append("duplicate in shard "+str(i))
        ids.add(key)
        if row.get("safety_grade") not in (None,""):
            errors.append("unreviewed candidate carries safety grade "+str(i))
        if row.get("feeding_safety_status") not in (None,"not_assessed"):
            errors.append("unreviewed candidate asserts feeding safety "+str(i))
        if row.get("feeding_record_status") in ("verified","confirmed","feeding_pending"):
            errors.append("unreviewed candidate asserts feeding record "+str(i))
    return {"file":path.relative_to(ROOT).as_posix(),"count":len(rows),"errors":errors[:30],"error_count":len(errors),"keys":list(ids)}
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--workers",type=int,default=20)
    args=ap.parse_args()
    if not 1<=args.workers<=32:ap.error("workers must be 1..32")
    old=read("data/taxonomy-shards/index.json")
    new=read("data/diverse_taxonomy_candidates.json")
    queue=read("data/evidence-first-queue/index.json")
    if old["count"]!=9995 or new["record_count"]!=len(new["records"]):
        raise SystemExit("FAIL: candidate manifest count")
    jobs=[("data/taxonomy-shards",x) for x in old["shards"]]
    jobs +=[("data/evidence-first-queue",x) for x in queue["shards"]]
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        reports=list(pool.map(inspect,jobs))
    errors=[{"file":r["file"],"errors":r["errors"],"error_count":r["error_count"]} for r in reports if r["error_count"]]
    oldkeys=[k for r in reports if r["file"].startswith("data/taxonomy-shards/") for k in r["keys"]]
    newkeys=[]
    for i,row in enumerate(new["records"]):
        name=row.get("scientific_name")
        if not name:errors.append({"file":"data/diverse_taxonomy_candidates.json","row":i,"error":"missing scientific name"})
        if row.get("safety_grade") not in (None,""):errors.append({"file":"data/diverse_taxonomy_candidates.json","row":i,"error":"safety grade on unreviewed candidate"})
        if row.get("feeding_safety_status") not in (None,"not_assessed"):errors.append({"file":"data/diverse_taxonomy_candidates.json","row":i,"error":"unsafe safety assertion"})
        newkeys.append(str(row.get("taxon_id") or name).casefold())
    for label,keys in (("legacy",oldkeys),("diverse",newkeys)):
        if len(keys)!=len(set(keys)):errors.append({"scope":label,"error":"duplicate IDs or names"})
    if len(oldkeys)!=9995:errors.append({"scope":"legacy","error":"count mismatch"})
    if sum(r["count"] for r in reports if r["file"].startswith("data/evidence-first-queue/"))!=queue["counts"]["unique_taxa_mentioned"]:
        errors.append({"scope":"evidence queue","error":"count mismatch"})
    report={"schema_version":"1.0","result":"FAIL" if errors else "PASS",
      "warning":"PASS validates integrity and absence of unauthorized safety claims; it does NOT certify scientific evidence or feeding suitability.",
      "legacy_candidates":len(oldkeys),"diverse_candidates":len(newkeys),
      "review_queue":queue["counts"]["unique_taxa_mentioned"],
      "checked_shards":len(reports),"errors":errors[:100],"error_count":len(errors)}
    dest=ROOT/"data/full_corpus_quality_report.json"
    dest.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False))
    return 1 if errors else 0
if __name__=="__main__":sys.exit(main())
