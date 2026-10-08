#!/usr/bin/env python3
"""Check all published plant details have grade-matched visible badge and safety rationale."""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
pages = sorted((ROOT / "plant").glob("*/index.html"))
errors = []
if not pages:
    errors.append("No generated plant detail pages found")

for page in pages:
    html = page.read_text(encoding="utf-8")
    section = re.search(r'<section class="card [^"]* decision"[^>]*>', html)
    if not section:
        errors.append(f"{page}: missing decision section")
        continue
    grade_match = re.search(r'data-grade="([^"]*)"', section.group())
    if not grade_match:
        errors.append(f"{page}: missing data-grade")
        continue
    grade = grade_match.group(1)
    badge = re.search(r'<span class="verdictbadge">([^<]+)</span>', html)
    if grade in "ABCD" and len(grade) == 1:
        if not badge or badge.group(1) != grade:
            errors.append(f"{page}: badge does not match {grade}")
        if not re.search(r'<span class="verdictlabel">[^<]+</span>', html):
            errors.append(f"{page}: missing visible grade meaning")
        if f'.decision[data-grade="{grade}"] .verdictbadge' not in html:
            errors.append(f"{page}: missing CSS for grade {grade}")
    elif badge:
        errors.append(f"{page}: ungraded verdict incorrectly shows grade badge")
    if 'class="decisionwhy ko-evidence"' not in html:
        errors.append(f"{page}: missing visible safety rationale")
    if 'href="#evidence"' not in html or 'id="evidence"' not in html:
        errors.append(f"{page}: missing evidence navigation")

if errors:
    print("\n".join(errors[:50]))
    print(f"FAIL: {len(errors)} problems across {len(pages)} pages")
    sys.exit(1)
print(f"PASS: grade badge, meaning, rationale, and evidence link checked across {len(pages)} pages")
