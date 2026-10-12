#!/usr/bin/env python3
"""Guard indexable catalog discovery against sitemap regeneration regressions."""
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://jinwooson1988.github.io/tortoise-food-db-korea/"
NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
tree = ET.parse(ROOT / "sitemap.xml")
urls = [node.text for node in tree.findall(".//sm:url/sm:loc", NS)]
assert len(urls) == len(set(urls)), "Duplicate sitemap URLs"
assert BASE + "all-plants/" in urls, "Indexable all-plants catalog missing from sitemap"
assert BASE + "en/all-plants/" not in urls, "Noindex English redirect included in sitemap"
assert all(url and url.startswith(BASE) for url in urls), "Unexpected sitemap origin"
page = (ROOT / "all-plants/index.html").read_text(encoding="utf-8")
assert '<meta name="robots" content="index,follow">' in page, "Catalog is not indexable"
assert f'<link rel="canonical" href="{BASE}all-plants/">' in page, "Catalog canonical mismatch"
redirect = (ROOT / "en/all-plants/index.html").read_text(encoding="utf-8")
assert 'content="noindex,follow"' in redirect, "English redirect indexability changed; revisit sitemap policy"
assert 'hreflang="en"' not in page, "Indexable catalog advertises English noindex redirect"
print(f"PASS: {len(urls)} sitemap URLs, canonical catalog and redirect policy")
