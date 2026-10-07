#!/usr/bin/env python3
"""Diagnostic-only audit of public plant-page information architecture.

This does not change verdicts, evidence, wording, or generated HTML. It gives the
UI redesign a reproducible baseline and can be run before/after template changes.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
PLANT_ROOT = ROOT / "plant"

ORDER = (
    ("decision", 'class="decision '),
    ("practical", 'class="card practical"'),
    ("nutrition", 'id="nutrition"'),
    ("evidence", 'class="card evidence-deep"'),
)

def main():
    pages = sorted(PLANT_ROOT.glob("*/index.html"))
    bad_order = []
    missing = []
    evidence_cards = []
    disclosure = []
    nested_style = []\n    touch_target_risks = []\n    horizontal_overflow_risks = []\n    tiny_text_risks = []\n    missing_landmarks = []\n    heading_order_risks = []\n    image_alt_risks = []

    for page in pages:
        text = page.read_text(encoding="utf-8")
        positions = {}
        for name, marker in ORDER:
            pos = text.find(marker)
            if pos < 0:
                missing.append((page.parent.name, name))
            positions[name] = pos

        present = [positions[name] for name, _ in ORDER if positions[name] >= 0]
        if present != sorted(present):
            bad_order.append(page.parent.name)

        cards = len(re.findall(r'class="evcard', text))
        evidence_cards.append((cards, page.parent.name))
        if cards >= 4:
            disclosure.append((page.parent.name, cards, "<details" in text))

        if re.search(r"</style>\s*</style>", text, re.I):
            nested_style.append(page.parent.name)

    evidence_cards.sort(reverse=True)
    dense = [(pid, n) for n, pid in evidence_cards if n >= 4]
    dense_without_disclosure = [(pid, n) for pid, n, has in disclosure if not has]

    print(f"public plant pages: {len(pages)}")
    print(f"missing core zones: {len(missing)}")
    print(f"wrong zone order: {len(bad_order)}")
    print(f"pages with >=4 evidence cards: {len(dense)}")
    print(f"dense pages without progressive disclosure: {len(dense_without_disclosure)}")
    print(f"malformed nested </style>: {len(nested_style)}")
    print(f"possible undersized interactive targets: {len(set(touch_target_risks))}")
    print(f"possible fixed-width mobile overflow: {len(set(horizontal_overflow_risks))}")
    print(f"pages using <=10px text: {len(set(tiny_text_risks))}")
    print(f"pages missing core semantic landmarks: {len(set(missing_landmarks))}")
    print(f"pages with heading-order risk: {len(set(heading_order_risks))}")
    print(f"pages with missing/empty image alt: {len(set(image_alt_risks))}")
    if evidence_cards:
        print("highest evidence-card counts:", ", ".join(f"{pid}={n}" for n, pid in evidence_cards[:10]))
    if missing:
        print("missing:", ", ".join(f"{pid}:{zone}" for pid, zone in missing[:20]))
    if bad_order:
        print("wrong order:", ", ".join(bad_order[:20]))
    if nested_style:
        print("nested style:", ", ".join(nested_style[:20]))

if __name__ == "__main__":
    main()
