#!/usr/bin/env python3
"""Regression guard: direct-evidence taxon detail must not await optional batch index."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
page = (ROOT / "taxon/index.html").read_text(encoding="utf-8")
checks = {
    "identity shard requested": "const shard=await j('../data/plant-catalog/taxa-'" in page,
    "direct evidence short circuit": "if(rec&&!directEvidence){" in page,
    "optional batch index requested only when needed": "batch002=await j('../data/catalog-evidence/batch-002-site-index.json');" in page,
    "no unconditional Promise.all dependency": "const [shard, batchIndex]=await Promise.all(" not in page,
    "loading failure shows error": "state='error';render();return" in page,
    "missing identity handled": "if(!rec){state='done';render();return}" in page,
}
for name, ok in checks.items():
    print(f"{'PASS' if ok else 'FAIL'} {name}")
if not all(checks.values()):
    raise SystemExit(1)
