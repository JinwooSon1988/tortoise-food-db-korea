#!/usr/bin/env python3
"""Install the prepared 9,995-record ZIP into the EXISTING repository checkout.
No network access, no Git commands, no edits to existing plant verdicts.
Usage: python scripts/install_taxonomy_package.py /path/to/gb9995_upload_ready.zip
Then: python scripts/verify_taxonomy_shards.py
"""
import hashlib,json,re,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/"data"/"taxonomy-shards"
def main():
    if len(sys.argv)!=2:raise SystemExit("Usage: install_taxonomy_package.py PACKAGE.zip")
    archive=Path(sys.argv[1])
    with zipfile.ZipFile(archive) as z:
        manifest_path="data/taxonomy-shards/index.json"
        manifest=json.loads(z.read(manifest_path))
        shards=manifest.get("shards",[])
        if manifest.get("count")!=9995 or len(shards)!=20:raise ValueError("unexpected dataset size")
        allowed={manifest_path}
        total=0;payloads={}
        for item in shards:
            filename=item["file"]
            if not re.fullmatch(r"taxa-[0-9]{2}\.json",filename):raise ValueError("invalid filename")
            path="data/taxonomy-shards/"+filename
            allowed.add(path)
            raw=z.read(path)
            if hashlib.sha256(raw).hexdigest()!=item["sha256"]:raise ValueError("SHA-256 mismatch: "+filename)
            rows=json.loads(raw)["records"]
            if len(rows)!=item["count"]:raise ValueError("record count mismatch")
            for r in rows:
                if r.get("safety_grade") not in (None,"") or r.get("feeding_safety_status") not in ("not_assessed",None):
                    raise ValueError("unreviewed species contains a feeding verdict")
            total+=len(rows)
            payloads[filename]=raw
        if set(z.namelist())!=allowed:raise ValueError("unexpected files in package")
        if total!=9995:raise ValueError("total record count mismatch")
        DEST.mkdir(parents=True,exist_ok=True)
        for name,raw in payloads.items():(DEST/name).write_bytes(raw)
        (DEST/"index.json").write_bytes(z.read(manifest_path))
    print("INSTALLED 9,995 records in 20 shards; no existing plant data changed")
if __name__=="__main__":main()
