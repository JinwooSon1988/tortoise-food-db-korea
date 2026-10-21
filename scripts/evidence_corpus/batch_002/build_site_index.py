"""Write data/catalog-evidence/batch-002-site-index.json from the batch 002 file: its records grouped by the printed
scientific name (lower case), with the batch's sources, as scripts/qa_batch_002_site.py expects. Run after make_batch_002.
Run from the repository root: python -X utf8 scripts/evidence_corpus/batch_002/build_site_index.py [batch file] [index file]
"""
import json, sys, collections
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
src = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data/catalog-evidence/batch-002-20261021.json"
out = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "data/catalog-evidence/batch-002-site-index.json"
b = json.loads(src.read_text(encoding="utf-8"))
grouped = collections.defaultdict(list)
for r in b["records"]:
    grouped[r["reported_name"].strip().casefold()].append(r)
index = {"schema_version": "1.0", "batch": b["batch"], "built": b["built"],
         "scope": "Exact scientific-name matches only; no feeding safety inferred", "sources": b["sources"],
         "by_scientific_name": dict(grouped),
         "stats": {"records": len(b["records"]), "distinct_reported_names": len(grouped), "held_not_linked": len(b["held_not_linked"])}}
out.write_text(json.dumps(index, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print(index["stats"])
