from pathlib import Path
import re,sys
ROOT=Path(__file__).resolve().parents[1]
g=(ROOT/"scripts/generate_static_pages.py").read_text(encoding="utf-8")
errors=[]
required=[
 "먼저 이것만 보세요.",
 "육지거북 사육을 전문적으로 다루는 자료",
 "이 자료가 지지하는 것:",
 "이 자료만으로 말할 수 없는 것:",
 "학술자료 · 원논문"
]
for s in required:
    if s not in g: errors.append("missing plain-language layer: "+s)
# Internal jargon that should not leak into Korean-facing explanatory copy.
for bad in ["전문 husbandry 자료","evidence dossier","applicability를","directness를"]:
    if bad in g: errors.append("untranslated jargon in public copy: "+bad)
# Scientific identifiers remain allowed and useful.
if "DOI" not in g or "PMID" not in g:
    errors.append("scientific identifiers unexpectedly removed")
if errors:
    print("FAIL: plain-Korean public writing contract")
    for e in errors: print("-",e)
    sys.exit(1)
print("PASS: plain-Korean layered explanation contract")
