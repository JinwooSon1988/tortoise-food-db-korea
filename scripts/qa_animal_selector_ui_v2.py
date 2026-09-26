from pathlib import Path
import json, re, sys
ROOT=Path(__file__).resolve().parents[1]
html=(ROOT/"index.html").read_text(encoding="utf-8")
reg=json.loads((ROOT/"data/animal_taxa_v1.json").read_text(encoding="utf-8"))
errors=[]
if 'id="animalSelect"' not in html: errors.append("animal selector missing")
for t in reg["taxa"]:
    if f'value="{t["id"]}"' not in html: errors.append(f'{t["id"]}: selector option missing')
    if t["scientific"]!="Testudo spp." and t["scientific"] not in html: errors.append(f'{t["id"]}: canonical scientific taxon missing from UI mapping')
if "다른 종의 판정을 자동 전이하지 않는다" not in html: errors.append("cross-taxon transfer warning missing")
if errors:
    print("FAIL: animal selector UI")
    for e in errors: print("-",e)
    sys.exit(1)
print(f'PASS: selector exposes {len(reg["taxa"])} canonical tortoise taxa with no-transfer warning')
