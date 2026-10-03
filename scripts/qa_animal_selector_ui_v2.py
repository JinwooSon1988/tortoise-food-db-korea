from pathlib import Path
import json, sys
ROOT=Path(__file__).resolve().parents[1]
html=(ROOT/"index.html").read_text(encoding="utf-8")
reg=json.loads((ROOT/"data/animal_taxa_v1.json").read_text(encoding="utf-8"))
assessments=json.loads((ROOT/"data/public_assessments.json").read_text(encoding="utf-8"))
if isinstance(assessments,dict): assessments=assessments.get("assessments",assessments.get("records",[]))
errors=[]
if 'id="animalSelect"' in html: errors.append("retired animal selector still exposed")
if "TV.speciesNotes(" not in html: errors.append("species-specific result notes missing")
if "종별 특이사항" not in html: errors.append("species-specific note label missing")
known={t["scientific"] for t in reg["taxa"]}
assessed={a.get("animal_taxon") for a in assessments if a.get("animal_taxon")}
if not {"Centrochelys sulcata","Testudo"}.issubset(assessed): errors.append("species-specific assessment data lost")
if "TV.speciesNotes(rowsFor(r.plant_id),a)" not in html: errors.append("species notes not wired into result rendering")
if errors:
    print("FAIL: plant-first species exception UI")
    for e in errors: print("-",e)
    sys.exit(1)
print(f"PASS: selector removed; {len(assessed)} assessed taxon labels retained and species exceptions surface in results")
