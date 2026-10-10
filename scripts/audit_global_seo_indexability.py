#!/usr/bin/env python3
"""Read-only SEO indexability checks for generated Korean and English pages."""
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://jinwooson1988.github.io/tortoise-food-db-korea"
NS = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
errors = []
tree = ET.parse(ROOT / "sitemap.xml")
urls = tree.findall(".//s:url", NS)
locs = [u.findtext("s:loc", namespaces=NS) for u in urls]
if len(locs) != len(set(locs)):
    errors.append("Duplicate sitemap locations")
if any(not u or not u.startswith(BASE + "/") for u in locs):
    errors.append("Sitemap contains out-of-scope URLs")
for url in locs:
    rel = url[len(BASE):].strip("/")
    page = ROOT / rel / "index.html" if rel else ROOT / "index.html"
    if not page.is_file():
        errors.append(f"Missing page: {url}")
        continue
    html = page.read_text(encoding="utf-8")
    if re.search(r'<meta[^>]+name=["\']robots["\'][^>]+content=["\'][^"\']*noindex', html, re.I):
        errors.append(f"Noindex URL in sitemap: {url}")
    canonical = re.search(r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)', html, re.I)
    if not canonical or canonical.group(1).rstrip("/") != url.rstrip("/"):
        errors.append(f"Canonical mismatch: {url}")
    if not re.search(r"<title>[^<]+</title>", html, re.I):
        errors.append(f"Missing title: {url}")
    if not re.search(r'<meta[^>]+name=["\']description["\']', html, re.I):
        errors.append(f"Missing description: {url}")
# Validate bilingual hreflang pairs for all indexed counterparts.
for url in locs:
    rel = url[len(BASE):].strip("/")
    if rel.startswith("en/"):
        ko_url, en_url = BASE + "/" + rel[3:].strip("/") + ("/" if rel[3:].strip("/") else ""), url
    else:
        ko_url, en_url = url, BASE + "/en/" + rel + ("" if rel.endswith("/") else "/")
    if ko_url not in locs or en_url not in locs:
        continue
    page = ROOT / rel / "index.html" if rel else ROOT / "index.html"
    html = page.read_text(encoding="utf-8")
    for lang, target in (("ko", ko_url), ("en", en_url)):
        expected = 'hreflang="' + lang + '" href="' + target + '"'
        if expected not in html:
            errors.append(f"Missing bilingual alternate {lang}: {url}")
if BASE + "/en/all-plants/" in locs:
    errors.append("Noindex English catalog redirect is in sitemap")
ko = {x[len(BASE):] for x in locs if "/en/" not in x[len(BASE):]}
en = {x[len(BASE + "/en"):] for x in locs if x.startswith(BASE + "/en/")}
for rel in en:
    if rel not in ko:
        errors.append(f"English URL lacks Korean counterpart: {rel}")
print(f"SEO indexability audit: {len(locs)} sitemap URLs, {len(en)} English URLs, {len(errors)} problems")
for e in errors[:60]:
    print("FAIL:", e)
sys.exit(bool(errors))
