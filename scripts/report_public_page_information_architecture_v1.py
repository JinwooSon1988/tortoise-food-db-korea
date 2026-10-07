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
    nested_style = []
    touch_target_risks = []
    horizontal_overflow_risks = []
    tiny_text_risks = []
    missing_landmarks = []
    heading_order_risks = []
    image_alt_risks = []

    for page in pages:
        text = page.read_text(encoding="utf-8")
        positions = {}
        for name, marker in ORDER:
            if name == "decision":
                # The decision card is rendered as class="card <tone> decision"; match the class token, not a prefix.
                m = re.search(r'class="[^"]*\bdecision\b[^"]*"', text)
                pos = m.start() if m else -1
            else:
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
            evidence_pos = text.find('class="card evidence-deep"')
            evidence_html = text[evidence_pos:] if evidence_pos >= 0 else ""
            disclosure.append((page.parent.name, cards, "<details" in evidence_html))

        if re.search(r"</style>\s*</style>", text, re.I):
            nested_style.append(page.parent.name)

        # Accessibility/mobile heuristics. These are intentionally conservative:
        # report only concrete markup/CSS patterns rather than pretending unmeasured
        # properties are zero-risk.
        if re.search(r'<(?:a|button|summary)\b[^>]*style="[^"]*(?:height|min-height)\s*:\s*(?:[0-3]?\d)px', text, re.I):
            touch_target_risks.append(page.parent.name)
        if re.search(r'(?:width|min-width)\s*:\s*(?:[7-9]\d\d|\d{4,})px', text, re.I) and "@media" not in text:
            horizontal_overflow_risks.append(page.parent.name)
        if re.search(r'font-size\s*:\s*(?:[1-9]|10)px', text, re.I):
            tiny_text_risks.append(page.parent.name)
        for landmark in ("<main", "<nav", "<footer"):
            if landmark not in text.lower():
                missing_landmarks.append((page.parent.name, landmark[1:]))
        headings = [int(x) for x in re.findall(r'<h([1-6])\b', text, re.I)]
        if any(b > a + 1 for a, b in zip(headings, headings[1:])):
            heading_order_risks.append(page.parent.name)
        if re.search(r'<img\b(?![^>]*\balt\s*=)[^>]*>', text, re.I) or re.search(r'<img\b[^>]*\balt\s*=\s*["\']\s*["\']', text, re.I):
            image_alt_risks.append(page.parent.name)

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
    print(f"missing core semantic landmarks: {len(set(missing_landmarks))}")
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

    if touch_target_risks:
        print("touch target risks:", ", ".join(sorted(set(touch_target_risks))[:20]))
    if horizontal_overflow_risks:
        print("overflow risks:", ", ".join(sorted(set(horizontal_overflow_risks))[:20]))
    if tiny_text_risks:
        print("tiny text:", ", ".join(sorted(set(tiny_text_risks))[:20]))
    if missing_landmarks:
        print("missing landmarks:", ", ".join(f"{pid}:{landmark}" for pid, landmark in sorted(set(missing_landmarks))[:20]))
    if heading_order_risks:
        print("heading order:", ", ".join(sorted(set(heading_order_risks))[:20]))
    if image_alt_risks:
        print("image alt:", ", ".join(sorted(set(image_alt_risks))[:20]))

if __name__ == "__main__":
    main()
