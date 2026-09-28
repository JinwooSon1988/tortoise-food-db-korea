#!/usr/bin/env python3
from pathlib import Path
import sys
root=Path(__file__).resolve().parents[1]
home=(root/"index.html").read_text(encoding="utf-8")
detail=(root/"plant-detail-v56.js").read_text(encoding="utf-8")
lang=(root/"language-toggle.js").read_text(encoding="utf-8")
checks={
 "home removes taxon selector": 'id="animalSelect"' not in home,
 "home exposes species-specific notes": "종별 특이사항" in home and "speciesNotes" in home,
 "home keeps scope labels": "육지거북 일반 근거" in home and "지중해 Testudo 근거" in home,
 "species-note label is bilingual": "'종별 특이사항':'Species-specific notes'" in lang,
 "retired selector translations removed": all(s not in lang for s in ("선택 종 판정 없음","선택 종 직접 판정","내 거북':'My tortoise","육지거북 선택","선택한 분류군의 근거만 우선 적용")),
 "detail retains evidence taxon handling": "tortoiseAnimalTaxon" in detail,
 "sulcata taxon retained in evidence/detail model": "Centrochelys sulcata" in detail,
 "leopard taxon retained in evidence/detail model": "Stigmochelys pardalis" in detail,
 "no fixed ibera heading": "왜 이베라에게 이렇게 판정했나?" not in detail,
 "detail selected-animal heading": "animal.ko" in detail,
}
bad=[k for k,v in checks.items() if not v]
if bad:
 print("FAIL: "+", ".join(bad)); sys.exit(1)
print("OK: homepage is plant-first; species-specific evidence remains visible without a selector")
