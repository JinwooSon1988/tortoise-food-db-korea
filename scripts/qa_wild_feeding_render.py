from pathlib import Path
import ast,json,re,sys
ROOT=Path(__file__).resolve().parents[1]
gen=ROOT/"scripts/generate_static_pages.py"
src=gen.read_text(encoding="utf-8")
errors=[]
try: ast.parse(src)
except SyntaxError as e: errors.append(f"generator syntax error: {e}")
wild=json.loads((ROOT/"data/wild_feeding_evidence.json").read_text(encoding="utf-8"))
records=wild.get("records",[])
if not records: errors.append("wild feeding evidence has no records")
required={"plant_id","tortoise_taxon","population_region","study_method","plant_part","feeding_signal","limitations"}
for i,r in enumerate(records):
    miss=required-set(r)
    if miss: errors.append(f"wild record {i} missing: {sorted(miss)}")
if 'wild_by_plant' not in src: errors.append("generator does not index wild evidence by plant")
if 'risk_by_plant' not in src: errors.append("generator does not index risk screening by plant")
if '근거 충돌 또는 안전성 미해결' not in src: errors.append("conflicting-evidence warning UI missing")
if 'publication_blocker' not in src: errors.append("risk publication blocker is not rendered")
if 'wild_section' not in src: errors.append("generator has no conditional wild section")
if '야생에서는 실제로 어떻게 먹었나?' not in src: errors.append("public wild-section heading missing")
if 'if wild_cards else ""' not in src: errors.append("wild section is not conditional")
if 'nutrition_section_no=6+section_offset' not in src: errors.append("dynamic section numbering missing")
berm=[r for r in records if r.get("plant_id")=="bermudagrass"]
if not berm: errors.append("bermudagrass reference wild record missing")
else:
    b=berm[0]
    if "Testudo graeca" not in b.get("tortoise_taxon",""): errors.append("bermudagrass target taxon regression")
    if not {"잎","줄기"} <= set(re.split(r"[·,/ ]+",b.get("plant_part",""))): errors.append("bermudagrass leaf/stem detail missing")
if errors:
    print("FAIL: wild feeding render QA")
    for e in errors: print("-",e)
    sys.exit(1)
print(f"PASS: wild feeding render QA ({len(records)} structured records)")
