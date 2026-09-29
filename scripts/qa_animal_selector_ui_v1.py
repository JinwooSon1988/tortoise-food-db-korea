#!/usr/bin/env python3
"""Plant-first UI: no species selector anywhere; species-specific evidence surfaces as notes."""
from pathlib import Path
import json, sys
root=Path(__file__).resolve().parents[1]
home=(root/"index.html").read_text(encoding="utf-8")
lang=(root/"language-toggle.js").read_text(encoding="utf-8")
gen=(root/"scripts/generate_static_pages.py").read_text(encoding="utf-8")
core=(root/"verdict-core.js").read_text(encoding="utf-8")
taxa={t["scientific"] for t in json.loads((root/"data/animal_taxa_v1.json").read_text(encoding="utf-8"))["taxa"]}
pages=[p.read_text(encoding="utf-8") for p in (root/"plant").glob("*/index.html")]
selector_tokens=("animalSelect","tortoiseAnimalTaxon","selectedAnimal","내 거북과 근거의 거리")
checks={
 "home removes taxon selector": all(t not in home for t in selector_tokens),
 "detail pages have no selector": all(t not in page for page in pages for t in selector_tokens),
 "home exposes species-specific notes": "종별 특이사항" in home and "TV.speciesNotes(" in home,
 "detail exposes species-specific notes": "종별 특이사항" in gen and "species_notes(rows,a)" in gen,
 "species notes never become the default verdict": "isSpeciesOnly" in core and "!isSpeciesOnly(x)" in core,
 "home keeps scope labels": "육지거북 일반 근거" in core and "지중해 Testudo 근거" in core,
 "species-note label is bilingual": "'종별 특이사항':'Species-specific notes'" in lang,
 "retired selector translations removed": all(s not in lang for s in ("선택 종 판정 없음","선택 종 직접 판정","내 거북':'My tortoise","육지거북 선택","선택한 분류군의 근거만 우선 적용")),
 "sulcata taxon retained in taxon registry": "Centrochelys sulcata" in taxa,
 "leopard taxon retained in taxon registry": "Stigmochelys pardalis" in taxa,
}
bad=[k for k,v in checks.items() if not v]
if bad:
 print("FAIL: "+", ".join(bad)); sys.exit(1)
print("OK: homepage is plant-first; species-specific evidence remains visible without a selector")
