#!/usr/bin/env python3
"""Fail CI when Korean/English homepages diverge from shared data and verdict contract."""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
KR = (ROOT / "index.html").read_text(encoding="utf-8")
EN = (ROOT / "en/index.html").read_text(encoding="utf-8")
EN_SEARCH = (ROOT / "en/search-en.js").read_text(encoding="utf-8")
errors = []
DATA = ("plants.json", "public_assessments.json", "verified_plant_images_v56.json")
for name, html in (("KR", KR), ("EN", EN)):
    if not re.search(r'<script[^>]+src=["\'](?:\.\./|\./)?verdict-core\.js', html):
        errors.append(f"{name}: shared verdict-core.js missing")
for name in DATA:
    if name not in KR:
        errors.append(f"KR: {name} not referenced")
    if name not in EN_SEARCH:
        errors.append(f"EN: {name} not referenced")
if "catalog_en.json" not in EN_SEARCH:
    errors.append("EN: translated catalog missing")
if "TortoiseVerdict" not in EN_SEARCH or "TortoiseVerdict" not in KR:
    errors.append("Both languages must use shared verdict engine")
if not re.search(r'<html[^>]+lang=["\']ko["\']', KR):
    errors.append("KR html lang missing")
if not re.search(r'<html[^>]+lang=["\']en["\']', EN):
    errors.append("EN html lang missing")
print("BILINGUAL SHARED CONTRACT:", "FAIL" if errors else "PASS")
for error in errors:
    print("-", error)
sys.exit(bool(errors))
