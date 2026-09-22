#!/usr/bin/env python3
from pathlib import Path
import sys
root=Path(__file__).resolve().parents[1]
home=(root/"index.html").read_text(encoding="utf-8")
detail=(root/"plant-detail-v56.js").read_text(encoding="utf-8")
checks={
 "home selector": 'id="animalSelector"' in home,
 "persistent selection home": "tortoiseAnimalTaxon" in home,
 "persistent selection detail": "tortoiseAnimalTaxon" in detail,
 "sulcata taxon": "Centrochelys sulcata" in home and "Centrochelys sulcata" in detail,
 "leopard taxon": "Stigmochelys pardalis" in home and "Stigmochelys pardalis" in detail,
 "no fixed ibera heading": "왜 이베라에게 이렇게 판정했나?" not in detail,
 "detail selected-animal heading": "animal.ko" in detail,
}
bad=[k for k,v in checks.items() if not v]
if bad:
 print("FAIL: "+", ".join(bad)); sys.exit(1)
print("OK: species selector persists from home search to plant detail; no cross-species verdict fallback for leopard")
