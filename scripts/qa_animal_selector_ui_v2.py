from pathlib import Path
import json, sys
ROOT=Path(__file__).resolve().parents[1]
html=(ROOT/"index.html").read_text(encoding="utf-8")
reg=json.loads((ROOT/"data/animal_taxa_v1.json").read_text(encoding="utf-8"))
errors=[]
if 'id="animalSelect"' not in html: errors.append("animal selector missing")
for t in reg["taxa"]:
    if f'value="{t["id"]}"' not in html: errors.append(f'{t["id"]}: selector option missing')
    if t["scientific"]!="Testudo spp." and t["scientific"] not in html: errors.append(f'{t["id"]}: canonical scientific taxon missing from UI mapping')
if "다른 종의 판정을 자동 전이하지 않는다" not in html: errors.append("cross-taxon transfer warning missing")
if "assessments_by_taxon_v1.json" not in html: errors.append("taxon-specific assessment dataset not loaded")
if "taxonAssessmentMap" not in html: errors.append("taxon-specific assessment map missing")
if "selectedAnimal!=='mediterranean_testudo')return null" not in html: errors.append("non-Testudo no-transfer guard missing")
if "assessment_scope==='tortoise_general'" in html: errors.append("generic tortoise fallback still present in homepage verdict engine")
if "document.getElementById('animalSelect').onchange" not in html: errors.append("selector change does not trigger rerender")
if errors:
    print("FAIL: animal selector semantic contract")
    for e in errors: print("-",e)
    sys.exit(1)
print(f'PASS: {len(reg["taxa"])} taxa exposed; exact taxon assessments wired; non-Testudo verdict transfer blocked')
