#!/usr/bin/env python3
from pathlib import Path
import sys
root=Path(__file__).resolve().parents[1]
home=(root/"index.html").read_text(encoding="utf-8")
detail=(root/"plant-detail-v56.js").read_text(encoding="utf-8")
checks={
 "home exposes current taxon selector": 'id="animalSelect"' in home,
 "home states no cross-taxon verdict transfer": "다른 종의 판정을 자동 전이하지 않는다" in home,
 "detail retains evidence taxon handling": "tortoiseAnimalTaxon" in detail,
 "sulcata taxon retained in evidence/detail model": "Centrochelys sulcata" in detail,
 "leopard taxon retained in evidence/detail model": "Stigmochelys pardalis" in detail,
 "no fixed ibera heading": "왜 이베라에게 이렇게 판정했나?" not in detail,
 "detail selected-animal heading": "animal.ko" in detail,
}
bad=[k for k,v in checks.items() if not v]
if bad:
 print("FAIL: "+", ".join(bad)); sys.exit(1)
print("OK: homepage exposes taxon selection without cross-taxon verdict transfer; detail evidence model retained")
