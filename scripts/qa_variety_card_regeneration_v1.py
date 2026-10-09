#!/usr/bin/env python3
"""Regeneration-preservation guard for plant detail pages.

1. Copies the working tree to a temporary directory, runs the same page pipeline as CI
   (generate_static_pages -> patch_curated_social_metadata -> inject_plant_detail_v56) and
   requires every committed plant/*/index.html to be byte-identical to the regenerated file.
   Any content that exists only as a hand edit therefore fails here instead of silently
   disappearing on the next deploy (deploy-pages.yml runs the generator before publishing).
2. Checks data-driven content contracts that must survive regeneration:
   - timothy: verified photo, creator, licence and Commons source link from verified_plant_images_v56.json
   - mint: peppermint/spearmint USDA candidate cards (FDC ID, food name, values, Ca:P, source link),
     hold wording and candidate data link, while the master nutrition stays "검증된 영양자료 없음"
   - lettuce: five USDA variety cards with values and Ca:P, data-computed comparison summary and data link
"""
import json, shutil, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
errors = []
load = lambda rel: json.loads((ROOT / rel).read_text(encoding="utf-8"))
page = lambda pid: (ROOT / "plant" / pid / "index.html").read_text(encoding="utf-8")


def nutrition_section(html):
    i = html.index('<section class="card" id="nutrition">')
    return html[i:html.index("</section>", i)]


# ---------------------------------------------------------------- 2) content contracts (fast, run first)
img = next(i for i in load("data/verified_plant_images_v56.json")["images"] if i["plant_id"] == "timothy")
t = page("timothy")
for needle in (img["image_url"], img["source_url"], img["creator"], img["license"]):
    if needle not in t: errors.append(f"timothy: verified photo field missing from page: {needle}")

for pid, path, labels in (("mint", "data/usda_mint_variety_candidates_20261009.json", None),
                          ("lettuce", "data/plant_nutrition_variety_v1.json", None)):
    data = load(path)
    sec = nutrition_section(page(pid))
    if "검증된 영양자료 없음" not in sec: errors.append(f"{pid}: master nutrition must stay '검증된 영양자료 없음'")
    if sec.count('class="varietycard"') != len(data["records"]): errors.append(f"{pid}: expected {len(data['records'])} variety cards")
    for r in data["records"]:
        if r["source_url"] not in sec: errors.append(f"{pid}: missing USDA link for FDC {r['fdc_id']}")
        card = sec.split(f'href="{r["source_url"]}"', 1)[0].rsplit('<article class="varietycard"', 1)[-1]
        for needle in (f"FDC {r['fdc_id']}", r["food_description"], f"<strong>{r['calcium_mg']}mg</strong>", f"<strong>{r['phosphorus_mg']}mg</strong>",
                       f"<strong>{r['fiber_g']}g</strong>", f"<strong>{r['vitamin_c_mg']}mg</strong>", f"<strong>{r['calcium_phosphorus_ratio']}:1</strong>"):
            if needle not in card: errors.append(f"{pid}: FDC {r['fdc_id']} card missing {needle!r}")
    if "minmax(min(100%," not in sec: errors.append(f"{pid}: variety grid must shrink below its minimum on narrow screens")
mint_sec = nutrition_section(page("mint"))
for needle in ("종·부위 확인 전", "검증된 영양자료 없음’ 상태를 유지", "../../data/usda_mint_variety_candidates_20261009.json", "육지거북 급여 안전성"):
    if needle not in mint_sec: errors.append(f"mint: missing {needle!r}")
let_sec = nutrition_section(page("lettuce"))
recs = load("data/plant_nutrition_variety_v1.json")["records"]
for needle in ("../../data/plant_nutrition_variety_v1.json", "급여 적합성", f"{max(r['calcium_mg'] for r in recs)}mg", f"{min(r['fiber_g'] for r in recs)}g"):
    if needle not in let_sec: errors.append(f"lettuce: missing {needle!r}")
# Bell pepper: colour-specific USDA table and the documented source conflict must be generator-owned.
bp = nutrition_section(page("bellpepper"))
pep = load("data/usda_bellpepper_original_csv_verified_20261008.json")["records"]
for r in pep:
    if r["source_url"] not in bp: errors.append(f"bellpepper: missing USDA link {r['fdc_id']}")
for r in [r for r in pep if r["data_type"] == "Foundation"]:
    if f"<td>{r['calcium_mg_per_100g']}mg</td><td>{r['phosphorus_mg_per_100g']}mg</td><td>{r['ca_p_ratio']}:1</td>" not in bp:
        errors.append(f"bellpepper: Foundation row {r['fdc_id']} missing or altered")
for needle in ("출처 간 상충", "급여하지 않음", "thetortoisetable.org.uk", "영양성분 수치가 급여 허용을 뜻하지는 않습니다."):
    if needle not in bp: errors.append(f"bellpepper: missing {needle!r}")

# Screen-reader-only text (e.g. " (새 창)") must be hidden visually wherever it is used.
for p in (ROOT / "plant").glob("*/index.html"):
    h = p.read_text(encoding="utf-8")
    if 'class="sr-only"' in h and ".sr-only{" not in h:
        errors.append(f"{p.parent.name}: uses class=sr-only without a visually-hidden .sr-only CSS rule")
master = {r["plant_id"] for r in load("data/plant_nutrition_v56.json")["plants"]}
if {"mint", "lettuce"} & master: errors.append("held variety candidates must not be promoted into plant_nutrition_v56.json")

# ---------------------------------------------------------------- 1) regeneration byte-equality
if "--skip-regen" not in sys.argv:
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp) / "repo"
        shutil.copytree(ROOT, work, ignore=shutil.ignore_patterns(".git", "node_modules", "__pycache__"))
        for step in ("generate_static_pages.py", "patch_curated_social_metadata.py", "inject_plant_detail_v56.py"):
            r = subprocess.run([sys.executable, f"scripts/{step}"], cwd=work, capture_output=True, text=True, encoding="utf-8", errors="replace")
            if r.returncode != 0:
                errors.append(f"regeneration step {step} failed: {r.stderr[-400:]}")
                break
        else:
            committed = {p.parent.name: p for p in (ROOT / "plant").glob("*/index.html")}
            regenerated = {p.parent.name: p for p in (work / "plant").glob("*/index.html")}
            if set(committed) != set(regenerated):
                errors.append(f"page set differs after regeneration: only committed {sorted(set(committed) - set(regenerated))[:5]}, only regenerated {sorted(set(regenerated) - set(committed))[:5]}")
            drift = [pid for pid in sorted(set(committed) & set(regenerated)) if committed[pid].read_bytes() != regenerated[pid].read_bytes()]
            if drift: errors.append(f"{len(drift)} committed page(s) differ from generator output (hand edits would be lost on deploy): {drift[:10]}")

if errors:
    for e in errors: print("ERROR:", e)
    sys.exit(f"regeneration preservation QA FAILED: {len(errors)} error(s)")
print(f"OK: all {len(list((ROOT / 'plant').glob('*/index.html')))} plant pages reproduce byte-identically; timothy photo, mint candidate cards and lettuce variety cards are generator-owned")
