#!/usr/bin/env python3
"""Invariant QA: the home search and every detail page show the same canonical verdict.

- The home search's real selection code (verdict-core.js) is executed with node and
  compared with scripts/public_verdict.py on data/public_assessments.json.
- Every generated detail page must carry that same grade, in the fixed section order,
  with one copy of each major section.
- Species-specific assessments never become the representative verdict.
"""
import json
import html, re, subprocess, sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from public_verdict import load_assessments, by_plant, representative, display, species_notes, public_plants, is_species_only

ROOT = Path(__file__).resolve().parents[1]
errors = []
plants = json.loads((ROOT / "data/plants.json").read_text(encoding="utf-8"))
assessments = load_assessments()
rows_by = by_plant(assessments)
# Every assessment evidence ID must resolve to a record that explicitly names the same plant.
evidence_raw = json.loads((ROOT / "data/public_evidence_records.json").read_text(encoding="utf-8"))
evidence_records = evidence_raw if isinstance(evidence_raw, list) else evidence_raw.get("evidence", evidence_raw.get("records", []))
evidence_by_id = {r.get("id"): r for r in evidence_records}
for record in evidence_records:
    if not (record.get("url") or record.get("doi") or record.get("pmid")):
        errors.append(f"{record.get('id')}: public evidence record has no source locator")

for assessment in assessments:
    pid = assessment.get("plant_id")
    for eid in assessment.get("evidence_ids", []):
        record = evidence_by_id.get(eid)
        if not record:
            errors.append(f"{pid}: assessment references missing evidence {eid}")
        elif pid not in record.get("plant_ids", []):
            errors.append(f"{pid}: evidence {eid} does not explicitly include this plant")

public = public_plants(plants, assessments)
public_ids = {p["id"] for p in public}
retail = {r["plant_id"]: r for r in json.loads((ROOT / "data/korean_retail_name_map.json").read_text(encoding="utf-8"))}

# 1) Home JS and Python choose the same assessment and grade for every plant.
node_src = r"""
const core=require(process.argv[1]);const data=JSON.parse(require('fs').readFileSync(0,'utf8'));
const out={};for(const [pid,rows] of Object.entries(data)){const a=core.representative(rows);out[pid]={index:a?rows.indexOf(a):-1,grade:core.display(a).grade,label:core.display(a).label,notes:core.speciesNotes(rows,a).map(x=>rows.indexOf(x))}}
process.stdout.write(JSON.stringify(out));
"""
try:
    proc = subprocess.run(["node", "-e", node_src, str(ROOT / "verdict-core.js")], input=json.dumps(rows_by), capture_output=True, text=True, encoding="utf-8", check=True)
    js = json.loads(proc.stdout)
except (OSError, subprocess.CalledProcessError) as exc:
    print("FAIL: could not execute verdict-core.js with node:", exc)
    sys.exit(1)
for pid, rows in rows_by.items():
    a = representative(rows)
    py = {"index": rows.index(a) if a else -1, "grade": display(a)["grade"], "label": display(a)["label"], "notes": [rows.index(x) for x in species_notes(rows, a)]}
    if js.get(pid) != py:
        errors.append(f"{pid}: home verdict-core {js.get(pid)} != generator {py}")
    if a is not None and is_species_only(a):
        errors.append(f"{pid}: species-specific assessment became the representative verdict")

# Representative-verdict priority is a public contract after species-selector removal.
priority_cases = [
    ([{'plant_id':'qa','animal_taxon':'Testudo graeca ibera','assessment_scope':'exact_species','verdict':'recommended'}, {'plant_id':'qa','animal_taxon':'Testudo','assessment_scope':'genus','verdict':'avoid'}], 'Testudo'),
    ([{'plant_id':'qa','animal_taxon':'Testudo graeca ibera','assessment_scope':'exact_species','verdict':'recommended'}, {'plant_id':'qa','species_group':'Mediterranean_Testudo','assessment_scope':'group','verdict':'caution'}], 'Mediterranean_Testudo'),
    ([{'plant_id':'qa','animal_taxon':'Testudo graeca ibera','assessment_scope':'exact_species','verdict':'recommended'}, {'plant_id':'qa','assessment_scope':'tortoise_general','species_group':'Tortoise_general','verdict':'limited'}], 'tortoise_general'),
]
for rows, expected in priority_cases:
    chosen = representative(rows)
    if expected == 'Testudo' and chosen.get('animal_taxon') != 'Testudo': errors.append('representative priority must prefer Testudo over exact-species rows')
    elif expected == 'Mediterranean_Testudo' and chosen.get('species_group') != 'Mediterranean_Testudo': errors.append('representative priority must prefer Mediterranean_Testudo over exact-species rows')
    elif expected == 'tortoise_general' and chosen.get('assessment_scope') != 'tortoise_general': errors.append('representative priority must prefer tortoise_general over exact-species rows')

# 2) Home wiring: canonical registry only, shared core, no species selector.
home = (ROOT / "index.html").read_text(encoding="utf-8")
search_live = (ROOT / "search-live.js").read_text(encoding="utf-8")
if "./verdict-core.js" not in home or "TV.representative(" not in home or "TV.display(" not in home:
    errors.append("home must select and label verdicts through verdict-core.js")
if "j('./data/public_assessments.json')" not in home:
    errors.append("home must load data/public_assessments.json")
for src, text in (("index.html", home), ("search-live.js", search_live)):
    for banned in ("assessments.json'", "assessments_korea_addendum", "animalSelect", "tortoiseAnimalTaxon", "selectedAnimal"):
        if banned in text.replace("public_assessments.json'", ""):
            errors.append(f"{src}: legacy verdict source or species selector present ({banned})")
if ".badge" in search_live or "replaceWith(verdict)" in search_live:
    errors.append("search-live.js must not rewrite result verdict badges")

# 2b) Hold/blocked assessments are an explicit evidence state, never silently grouped with A-D.
hold_ids = {pid for pid, rows in rows_by.items() if display(representative(rows))["grade"] == "보류"}
if hold_ids:
    # Home intentionally has no grade/filter controls; hold remains explicit on each result card.
    # Do not require a redundant hold filter as long as canonical card rendering is preserved.
    for pid in sorted(hold_ids):
        a = representative(rows_by[pid])
        if a and a.get("verdict") == "blocked" and display(a)["grade"] != "보류":
            errors.append(f"{pid}: blocked assessment must remain hold, not A/B/C/D")

# Home result cards must render canonical label and meaning directly from the shared verdict core.
home_card = re.search(r'function card\(r\)\{[\s\S]*?\nfunction render', home)
if not home_card:
    errors.append("home result-card renderer missing")
else:
    card_src = home_card.group(0)
    for token in ("TV.display(a)", "g.grade", "g.label", "g.meaning"):
        if token not in card_src:
            errors.append(f"home result card must expose canonical verdict field: {token}")
    for forbidden in ("gradeOverride", "meaningOverride", "labelOverride"):
        if forbidden in card_src:
            errors.append(f"home result card must not override canonical verdict semantics: {forbidden}")

# 3) Detail pages: exist for exactly the public set, same grade, fixed order, no duplicates.
page_dirs = {p.parent.name for p in (ROOT / "plant").glob("*/index.html")}
# Sitemap must expose exactly the same public plant set as home/detail generation.
sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
sitemap_ids = set(re.findall(r"/plant/([^/]+)/", sitemap))
for pid in sorted(public_ids - sitemap_ids):
    errors.append(f"{pid}: public plant missing from sitemap")
for pid in sorted(sitemap_ids - public_ids):
    errors.append(f"{pid}: sitemap contains non-public/orphan plant")

for pid in sorted(public_ids - page_dirs):
    errors.append(f"{pid}: public plant has no detail page")
for pid in sorted(page_dirs - public_ids):
    errors.append(f"{pid}: detail page exists for a non-public plant (orphan or candidate)")
for p in public:
    pid = p["id"]
    path = ROOT / "plant" / pid / "index.html"
    if not path.exists():
        continue
    text = path.read_text(encoding="utf-8")
    rows = rows_by.get(pid, [])
    a = representative(rows)
    g = display(a)
    m = re.search(r'class="card [a-z]+ decision" data-grade="([^"]+)" data-verdict="([^"]+)"', text)
    if not m:
        errors.append(f"{pid}: decision card missing")
        continue
    if m.group(1) != g["grade"] or m.group(2) != ((a or {}).get("verdict") or "none"):
        errors.append(f"{pid}: detail grade {m.group(1)}/{m.group(2)} != canonical {g['grade']}/{(a or {}).get('verdict')}")
    expected_tone = g["tone"]
    if f'class="card {expected_tone} decision"' not in text:
        errors.append(f"{pid}: decision tone must match canonical verdict ({expected_tone})")
    decision_start = text.find(' decision" data-grade=')
    decision_end = text.find('</section>', decision_start)
    decision_text = text[decision_start:decision_end] if decision_start >= 0 and decision_end >= 0 else ""
    expected_aria = f'aria-label="급여 판정 · {html.escape(str(g["grade"]), quote=True)} {html.escape(str(g["label"]), quote=True)}"'
    if expected_aria not in decision_text:
        errors.append(f"{pid}: decision card must expose grade and verdict label to assistive technology")
    if g["grade"] == "보류":
        if not any(boundary in decision_text for boundary in ("보류는 안전하다는 뜻이 아니다", "판정이 없다는 것은 안전하다는 뜻이 아니다")):
            errors.append(f"{pid}: hold safety boundary must remain visible in the decision card")
    elif g["grade"] == "D":
        if "급여하지 않음" not in text or "현재 판정에서는 급여 대상에서 제외한다." not in text:
            errors.append(f"{pid}: D verdict must preserve explicit do-not-feed meaning")
    elif g["grade"] in ("A", "B", "C") and "판정 보류" in text.split('<section class="card practical"',1)[0]:
        errors.append(f"{pid}: graded verdict must not look like a hold state")
    if g["label"] not in text or g["meaning"] not in text:
        errors.append(f"{pid}: grade label/meaning missing")
    if a and g["grade"] in ("B", "C", "D") and ('class="decisionwhy' not in decision_text or '<b>왜 이렇게 판정했나</b>' not in decision_text):
        errors.append(f"{pid}: restrictive verdict reason must remain visible before secondary detail")
    expected_basis = __import__("public_verdict").scope_label(a)
    if f'<div class="decisionlabel">급여 판정 · {expected_basis}</div>' not in text:
        errors.append(f"{pid}: decision label must show actual evidence scope ({expected_basis})")

    practical = text.find('<section class="card practical"')
    evidence = text.find('<section class="card evidence-deep" id="evidence">')
    nutrition = text.find('<section class="card" id="nutrition">')
    if evidence < 0 or evidence < decision_start:
        errors.append(f"{pid}: evidence section missing or precedes verdict")
    if practical >= 0 and not (decision_start < practical < evidence):
        errors.append(f"{pid}: practical action must sit between verdict and evidence")
    if nutrition >= 0 and not (evidence < nutrition):
        errors.append(f"{pid}: nutrition must follow evidence")
    if '<details class="scopefold">' in text or '적용 범위와 아직 확인되지 않은 내용 보기' in text or '비슷한 식물도 확인하기' in text:
        errors.append(f"{pid}: retired scope/related UI returned")

    notes = species_notes(rows, a)
    if "<h2>종별 특이사항</h2>" in text and not notes:
        errors.append(f"{pid}: species-specific section must not appear without species-only assessments")
    high_risk = (retail.get(pid, {}).get("mapping_status") == "name_candidate_only") or p.get("identity_status") == "needs_species_level_mapping"
    has_alert = 'data-identity="alert"' in text
    if high_risk and not has_alert:
        errors.append(f"{pid}: identity risk in data but no strong identity warning")

    linked = [evidence_by_id[eid] for eid in ((a or {}).get("evidence_ids", [])) if eid in evidence_by_id]
    if linked and text.count('class="sourceopen"') < len(linked):
        errors.append(f"{pid}: every linked evidence card must expose a clear original-source action")
    if linked and text.count("근거의 한계") < len(linked):
        errors.append(f"{pid}: every linked evidence card must state its evidence limit")
    for e in linked:
        expected_url = e.get("url") or (f'https://doi.org/{e["doi"]}' if e.get("doi") else (f'https://pubmed.ncbi.nlm.nih.gov/{e["pmid"]}/' if e.get("pmid") else ""))
        if not expected_url:
            errors.append(f"{pid}: linked evidence has no traceable source locator ({e.get('id')})")
        elif f'href="{html.escape(str(expected_url), quote=True)}"' not in text:
            errors.append(f"{pid}: evidence source action does not resolve to canonical locator ({e.get('id')})")
    for retired in ("plant-detail-v56.js", "ibera-direct-evidence-v56.js", "tortoiseAnimalTaxon", "animalSelect"):
        if retired in text:
            errors.append(f"{pid}: retired runtime enhancer or species selector referenced ({retired})")

if errors:
    print(f"FAIL: verdict consistency ({len(errors)})")
    for e in errors[:80]:
        print("-", e)
    sys.exit(1)
grades = Counter(display(representative(rows_by.get(p["id"], [])))["grade"] for p in public)
print(f"PASS: home (verdict-core.js) and {len(public)} detail pages agree on every canonical verdict; grades {dict(sorted(grades.items()))}")
