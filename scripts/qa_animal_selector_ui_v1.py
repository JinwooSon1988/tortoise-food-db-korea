#!/usr/bin/env python3
from pathlib import Path
import sys
root=Path(__file__).resolve().parents[1]
home=(root/"index.html").read_text(encoding="utf-8")
detail=(root/"plant-detail-v56.js").read_text(encoding="utf-8")
checks={
 "home uses shared Mediterranean diet context": "지중해형 육지거북 먹이 DB" in home,
 "home has no species selector": 'id="animalSelector"' not in home,
 "home does not persist species choice": "tortoiseAnimalTaxon" not in home,
 "detail retains evidence taxon handling": "tortoiseAnimalTaxon" in detail,
 "sulcata taxon retained in evidence/detail model": "Centrochelys sulcata" in detail,
 "leopard taxon retained in evidence/detail model": "Stigmochelys pardalis" in detail,
 "no fixed ibera heading": "왜 이베라에게 이렇게 판정했나?" not in detail,
 "detail selected-animal heading": "animal.ko" in detail,
}
bad=[k for k,v in checks.items() if not v]
if bad:
 print("FAIL: "+", ".join(bad)); sys.exit(1)
print("OK: homepage uses shared Mediterranean-type feeding context; taxon-specific evidence remains available in detail model")
