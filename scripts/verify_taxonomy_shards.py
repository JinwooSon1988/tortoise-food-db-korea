#!/usr/bin/env python3
"""Validate uploaded taxonomy shards, manifest digests and safety boundaries.
No network or third-party dependencies. Exits nonzero on any mismatch.
"""
import hashlib,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"data/taxonomy-shards"
def main():
    manifest=json.loads((BASE/"index.json").read_text(encoding="utf-8"))
    seen_names=set();seen_keys=set();total=0
    for entry in manifest["shards"]:
        name=entry["file"]
        if not re.fullmatch(r"taxa-\\d{2}\\.json",name):raise ValueError("unsafe shard filename")
        raw=(BASE/name).read_bytes()
        digest=hashlib.sha256(raw).hexdigest()
        if digest!=entry["sha256"]:raise ValueError(f"hash mismatch: {name}")
        payload=json.loads(raw)
        records=payload["records"]
        if len(records)!=entry["count"]:raise ValueError(f"count mismatch: {name}")
        for r in records:
            scientific=r["scientific_name"];taxon=r["taxon_id"]
            if scientific.casefold() in seen_names or taxon in seen_keys:raise ValueError("duplicate taxon")
            if not re.fullmatch(r"gbif:\\d+",taxon):raise ValueError("invalid GBIF id")
            if r.get("safety_grade") not in (None,"") or r.get("feeding_safety_status") not in ("not_assessed",None):
                raise ValueError("unreviewed candidate given feeding grade")
            if r.get("feeding_record_status") in ("record_under_review","verified") and not r.get("feeding_record_evidence"):
                raise ValueError("feeding record status without linked evidence")
            seen_names.add(scientific.casefold());seen_keys.add(taxon)
        total+=len(records)
    if total!=manifest["count"] or total!=9995:raise ValueError(f"total mismatch: {total}")
    print(f"PASS: {total} unique GBIF taxa, {len(manifest['shards'])} hash-verified shards, no inferred safety grades")
if __name__=="__main__":
    try:main()
    except (OSError,ValueError,KeyError,TypeError) as e:
        print("FAIL:",e,file=sys.stderr);sys.exit(1)
