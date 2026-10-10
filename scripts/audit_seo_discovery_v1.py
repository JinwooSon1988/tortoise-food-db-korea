#!/usr/bin/env python3
"""Read-only SEO audit. Does not rewrite pages, routes, translations, or data."""
import re
import json
from pathlib import Path
from xml.etree import ElementTree as ET
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://jinwooson1988.github.io/tortoise-food-db-korea/"
NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
sitemap = ET.parse(ROOT / "sitemap.xml").getroot()
urls = [node.text for node in sitemap.findall(".//sm:loc", NS)]
problems = []
if len(urls) != len(set(urls)):
    problems.append("duplicate sitemap loc URLs")
counts = Counter()
for url in urls:
    if not url.startswith(BASE):
        problems.append(f"outside project origin: {url}")
        continue
    relative = url[len(BASE):]
    file = ROOT / relative / "index.html" if relative else ROOT / "index.html"
    if not file.exists():
        problems.append(f"missing index.html for sitemap URL: {relative}")
        continue
    html = file.read_text(encoding="utf-8")
    title = re.search(r"<title>(.*?)</title>", html, re.I | re.S)
    description = re.search(r'<meta\s+name="description"\s+content="([^"]*)"', html, re.I)
    canonical = re.search(r'<link\s+rel="canonical"\s+href="([^"]+)"', html, re.I)
    robots = re.search(r'<meta\s+name="robots"\s+content="([^"]+)"', html, re.I)
    if not title or not title.group(1).strip():
        problems.append(f"missing title: {relative}")
    if not description or not description.group(1).strip():
        problems.append(f"missing description: {relative}")
    if not canonical:
        problems.append(f"missing canonical: {relative}")
    elif canonical.group(1) != url:
        problems.append(f"canonical mismatch (possibly redirect/noindex): {relative} -> {canonical.group(1)}")
    if robots and "noindex" in robots.group(1).lower():
        problems.append(f"noindex URL listed in sitemap: {relative}")
    counts["en" if relative.startswith("en/") or relative == "en/" else "ko"] += 1

print(json.dumps({"sitemap_urls": len(urls), "languages": dict(counts),
                  "problems": problems, "problem_count": len(problems)},
                 ensure_ascii=False, indent=2))
# Discovery audit is diagnostic: do not fail deployment on known pre-existing issues.
