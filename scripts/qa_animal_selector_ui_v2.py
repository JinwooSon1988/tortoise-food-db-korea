from pathlib import Path
import json, sys
ROOT=Path(__file__).resolve().parents[1]
html=(ROOT/"index.html").read_text(encoding="utf-8")
reg=json.loads((ROOT/"data/animal_taxa_v1.json").read_text(encoding="utf-8"))
assessments=[]
for p in [ROOT/"data/assessments.json", *sorted((ROOT/"data").glob("assessments_korea_addendum*.json"))]:
    if p.exists(): assessments += json.loads(p.read_text(encoding="utf-8"))
errors=[]
if 'id="animalSelect"' in html: errors.append("retired animal selector still exposed")
if "function speciesNotes(id,primary)" not in html: errors.append("species-specific result notes missing")
if "종별 특이사항" not in html: errors.append("species-specific note label missing")
known={t["scientific"] for t in reg["taxa"]}
assessed={a.get("animal_taxon") for a in assessments if a.get("animal_taxon")}
if not {"Centrochelys sulcata","Testudo"}.issubset(assessed): errors.append("species-specific assessment data lost")
if "speciesNotes(r.plant_id,a)" not in html: errors.append("species notes not wired into result rendering")
if errors:
    print("FAIL: plant-first species exception UI")
    for e in errors: print("-",e)
    sys.exit(1)
print(f"PASS: selector removed; {len(assessed)} assessed taxon labels retained and species exceptions surface in results")
