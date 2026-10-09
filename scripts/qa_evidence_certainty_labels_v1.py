#!/usr/bin/env python3
"""Evidence certainty (assessment `confidence`) is shown in words, never as a letter next to the A–D feeding grade.

Checks:
  * the inlined CERTAINTY_KO maps in index.html and all-plants/index.html equal scripts/evidence_certainty.py;
  * no public page renders "근거 확실성" / "근거 수준" / "근거등급" followed by a bare letter code;
  * every published detail page carries the certainty line with the word for its representative assessment;
  * the research-method page explains that certainty and the feeding grade are different (anchor #certainty).
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from evidence_certainty import CERTAINTY_KO, certainty_ko  # noqa: E402
from public_verdict import load_assessments, by_plant, representative, public_plants  # noqa: E402

errors = []
for p in ("index.html", "all-plants/index.html"):
    s = (ROOT / p).read_text(encoding="utf-8")
    m = re.search(r"const CERTAINTY_KO=(\{.*?\});", s)
    if not m or json.loads(m.group(1)) != CERTAINTY_KO:
        errors.append(f"{p}: CERTAINTY_KO differs from scripts/evidence_certainty.py")
BARE = re.compile(r"(근거 확실성|근거 수준|근거등급)\s*:?\s*(<b>)?\s*[ABCD][+-]?\s*(</b>|<|·|$)")
pages = list((ROOT / "plant").glob("*/index.html")) + list((ROOT / "guides").glob("*/index.html")) + [ROOT / "index.html", ROOT / "all-plants/index.html"]
for p in pages:
    s = p.read_text(encoding="utf-8")
    if BARE.search(s):
        errors.append(f"{p.relative_to(ROOT)}: certainty shown as a bare letter code")
plants = json.loads((ROOT / "data/plants.json").read_text(encoding="utf-8"))
assess = load_assessments(); rows = by_plant(assess)
n = 0
for pl in public_plants(plants, assess):
    a = representative(rows.get(pl["id"]))
    f = ROOT / "plant" / pl["id"] / "index.html"
    if not a or not f.exists():
        continue
    n += 1
    want = f'<p class="certaintyline">근거 확실성 <b>{certainty_ko(a.get("confidence"))}</b>'
    if want not in f.read_text(encoding="utf-8"):
        errors.append(f"{pl['id']}: certainty line missing or wrong (expected {certainty_ko(a.get('confidence'))})")
rm = (ROOT / "guides/research-method/index.html").read_text(encoding="utf-8")
if 'id="certainty"' not in rm or "근거 확실성은 급여 등급과 다르다" not in rm:
    errors.append("research-method: certainty explanation (#certainty) missing")
if errors:
    for e in errors[:40]: print("ERROR:", e)
    sys.exit(f"evidence certainty label QA FAILED: {len(errors)} error(s)")
print(f"OK: certainty shown in words on {n} detail pages, hubs, home and catalog; maps identical; research-method explains it")
