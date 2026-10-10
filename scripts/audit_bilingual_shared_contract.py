#!/usr/bin/env python3
"""Fail CI when Korean/English homepages diverge from shared data and verdict contract."""
from pathlib import Path
import re
import sys
import json
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
KR = (ROOT / "index.html").read_text(encoding="utf-8")
EN = (ROOT / "en/index.html").read_text(encoding="utf-8")
EN_SEARCH = (ROOT / "en/search-en.js").read_text(encoding="utf-8")
errors = []
# Primary user experience is ONE homepage with an in-place language toggle.
# The legacy /en/ pages are not the language switch destination.
TOGGLE = (ROOT / "language-toggle.js").read_text(encoding="utf-8")
if not re.search(r'<button[^>]+data-lang=["\\\']ko["\\\']', KR):
    errors.append("KR: missing same-page Korean language button")
if not re.search(r'<button[^>]+data-lang=["\\\']en["\\\']', KR):
    errors.append("KR: missing same-page English language button")
if re.search(r'<nav[^>]*class=["\\\']langswitch["\\\'][^>]*>.*?<a[^>]+href=["\\\'][^"\\\']*en/', KR, re.S):
    errors.append("KR: language switch must not navigate to /en/")
if "tfdblanguagechange" not in TOGGLE or "tfdblanguagechange" not in KR:
    errors.append("KR: in-place language event must update rendered search results")
if "data/i18n/en/catalog_en.json" not in KR:
    errors.append("KR: shared search must load English translations")

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
# The English catalog must be a translation layer over the same plant IDs, never a separate catalog.
plants = json.loads((ROOT / "data/plants.json").read_text(encoding="utf-8"))
translations = json.loads((ROOT / "data/i18n/en/catalog_en.json").read_text(encoding="utf-8"))["plants"]
source_ids = [p.get("id") for p in plants]
translated_ids = [p.get("id") for p in translations]
for label, ids in (("source", source_ids), ("English", translated_ids)):
    for pid, count in Counter(ids).items():
        if count > 1:
            errors.append(f"{label}: duplicate plant ID {pid}")
for pid in sorted(set(source_ids) - set(translated_ids)):
    errors.append(f"EN: missing plant translation {pid}")
for pid in sorted(set(translated_ids) - set(source_ids)):
    errors.append(f"EN: orphan translation {pid}")
for item in translations:
    pid = item.get("id", "<missing>")
    for field in ("name", "why", "role"):
        value = item.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"EN: {pid} missing {field}")
print("BILINGUAL SHARED CONTRACT:", "FAIL" if errors else "PASS")
for error in errors:
    print("-", error)
sys.exit(bool(errors))
