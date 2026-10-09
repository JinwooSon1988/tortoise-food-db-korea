#!/usr/bin/env python3
"""QA for the '급여 시 주의할 점' card on plant detail pages (run after the canonical generator pipeline).

For every published plant page with assessment limits:
  * the card follows the verdict (decision) and 'how to feed' cards and precedes nutrition and evidence, so the
    grade and core explanation stay first on screen;
  * the number of shown cautions equals the de-duplicated limits, and no caution is repeated;
  * every shown caution sits in the group scripts/feeding_cautions.py assigns to it; hazards, scope and feeding
    method are visible, evidence gaps are folded in <details>;
  * nothing worded as an evidence limitation ("…시험이 아님", "…로 단정하지 않음") appears as a confirmed hazard;
  * the verdict card and cautions carry no English specialist verdict label.
"""
import html, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from feeding_cautions import classify, dedupe, localize_specialist_labels, SPECIALIST_LABEL_KO, INTERPRETIVE, DIRECTIVE  # noqa: E402
from public_verdict import load_assessments, by_plant, representative, public_plants  # noqa: E402

errors, checked, shown = [], 0, 0
plants = json.loads((ROOT / "data/plants.json").read_text(encoding="utf-8"))
assess = load_assessments()
rows_by = by_plant(assess)
text_of = lambda frag: html.unescape(re.sub(r"<[^>]+>", "", frag)).strip()

for p in public_plants(plants, assess):
    pid = p["id"]; a = representative(rows_by.get(pid))
    page_path = ROOT / "plant" / pid / "index.html"
    if not a or not page_path.exists():
        continue
    page = page_path.read_text(encoding="utf-8")
    expected = dedupe(localize_specialist_labels(x) for x in (a.get("limits") or []))
    checked += 1
    if not expected:
        if 'id="cautions"' in page: errors.append(f"{pid}: cautions card without limits")
        continue
    if page.count('id="cautions"') != 1:
        errors.append(f"{pid}: expected exactly one cautions card"); continue
    pos = {"decision": page.find(' decision" data-grade='), "practical": page.find('class="card practical"'),
           "cautions": page.find('id="cautions"'), "nutrition": page.find('id="nutrition"'), "evidence": page.find('id="evidence"')}
    if not (0 <= pos["decision"] < pos["practical"] < pos["cautions"] < pos["nutrition"] < pos["evidence"]):
        errors.append(f"{pid}: cautions card out of order {pos}")
    start = pos["cautions"]; card = page[start:page.index("</section>", start)]
    items = []
    for m in re.finditer(r'<(div|details) class="(cautiongroup cg-\w+|cautionevidence)" data-caution="(\w+)">(.*?)</\1>', card, re.S):
        tag, _, key, body = m.groups()
        if (key == "evidence") != (tag == "details"):
            errors.append(f"{pid}: group {key} must be {'folded' if key == 'evidence' else 'visible'}")
        for li in re.findall(r"<li>(.*?)</li>", body, re.S):
            t = text_of(li); items.append(t)
            if classify(t) != key:
                errors.append(f"{pid}: '{t[:50]}' shown under {key}, classifier says {classify(t)}")
            if key == "risk" and INTERPRETIVE.search(DIRECTIVE.sub("", t)):
                errors.append(f"{pid}: evidence-limitation wording shown as a hazard: {t[:60]}")
    shown += len(items)
    if len(items) != len(set(items)):
        errors.append(f"{pid}: duplicated caution")
    if len(items) != len(expected):
        errors.append(f"{pid}: {len(items)} cautions shown, {len(expected)} de-duplicated limits expected")
    reader = page[pos["decision"]:pos["nutrition"]]
    for leaked in SPECIALIST_LABEL_KO:
        if leaked in reader:
            errors.append(f"{pid}: English specialist label in reader-facing assessment text: {leaked}")

if errors:
    for e in errors[:40]: print("ERROR:", e)
    sys.exit(f"feeding cautions QA FAILED: {len(errors)} error(s)")
print(f"OK: {checked} plant pages; {shown} de-duplicated cautions shown once in the right group, after the verdict and feeding cards")
