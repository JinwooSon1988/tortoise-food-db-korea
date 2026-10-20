#!/usr/bin/env python3
"""Build small, deterministic, review-safe taxonomy shards for static hosting.
Input: data/global_taxonomy_candidates.json
Outputs: data/taxonomy-shards/index.json and 20 shard files.
Existing feeding grades and existing plant pages are not modified.
"""
import json, math, re, hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"data/global_taxonomy_candidates.json"
DEST=ROOT/"data/taxonomy-shards"
def main():
    obj=json.loads(SRC.read_text(encoding="utf-8"))
    rows=obj["records"] if isinstance(obj,dict) else obj
    if len(rows)!=9995:raise SystemExit(f"expected 9995 records, found {len(rows)}; aborting")
    names=set();keys=set()
    for i,r in enumerate(rows):
        name=r.get("scientific_name","")
        key=r.get("taxon_id","")
        if not re.match(r"^[A-Z][a-z-]+ [a-z][a-z-]+(?: .*)?$",name):raise SystemExit(f"invalid scientific name at {i}")
        if not re.fullmatch(r"gbif:\d+",key):raise SystemExit(f"invalid GBIF key at {i}")
        if name.casefold() in names or key in keys:raise SystemExit(f"duplicate identity at {i}")
        if r.get("feeding_safety_status") not in ("not_assessed",None) or r.get("safety_grade") not in (None,""):
            raise SystemExit(f"unsafe candidate verdict at {i}")
        names.add(name.casefold());keys.add(key)
    rows=sorted(rows,key=lambda r:(r["scientific_name"].casefold(),r["taxon_id"]))
    DEST.mkdir(parents=True,exist_ok=True)
    manifest=[]
    for idx in range(20):
        chunk=rows[idx*500:(idx+1)*500]
        path=DEST/f"taxa-{idx+1:02d}.json"
        raw=json.dumps({"schema_version":"1.0","records":chunk},ensure_ascii=False,separators=(",",":"))+"\n"
        path.write_text(raw,encoding="utf-8")
        manifest.append({"file":path.name,"count":len(chunk),"sha256":hashlib.sha256(raw.encode()).hexdigest()})
    for stale in DEST.glob("taxa-*.json"):
        if stale.name not in {m["file"] for m in manifest}:stale.unlink()
    (DEST/"index.json").write_text(json.dumps({"schema_version":"1.0","count":len(rows),"shards":manifest},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Validated {len(rows)} candidates and wrote {len(manifest)} shards; no feeding verdicts assigned")
if __name__=="__main__":main()
