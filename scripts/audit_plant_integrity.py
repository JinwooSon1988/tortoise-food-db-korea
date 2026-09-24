#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
PLANTS = ROOT / "data" / "plants.json"
PLANT_DIR = ROOT / "plant"
SITEMAP = ROOT / "sitemap.xml"
BASE = "https://jinwooson1988.github.io/tortoise-food-db-korea/"


def fail(msg: str) -> None:
    print(f"FAIL: {msg}")


def main() -> int:
    errors: list[str] = []
    plants = json.loads(PLANTS.read_text(encoding="utf-8"))
    ids = [p.get("id") for p in plants]
    if any(not x for x in ids):
        errors.append("plants.json contains missing/empty id")
    dup_ids = [k for k, v in Counter(ids).items() if v > 1]
    if dup_ids:
        errors.append(f"duplicate plant ids: {dup_ids}")

    id_set = set(ids)
    # Only reviewed/public records are required to have indexable detail pages.\n    # Candidate/unreviewed records stay in the searchable intake catalog without\n    # creating thin SEO pages or implying a feeding verdict.\n    public_ids = {p["id"] for p in plants if p.get("suitability_status") != "unreviewed" and p.get("identity_status") != "candidate_name"}\n    dirs = {p.name for p in PLANT_DIR.iterdir() if p.is_dir() and (p / "index.html").exists()}
    missing_pages = sorted(public_ids - dirs)
    extra_pages = sorted(dirs - id_set)
    if missing_pages:
        errors.append(f"missing plant detail pages: {missing_pages}")
    if extra_pages:
        errors.append(f"detail pages without plants.json id: {extra_pages}")

    xml = SITEMAP.read_text(encoding="utf-8")
    locs = re.findall(r"<loc>(.*?)</loc>", xml)
    dup_locs = [k for k, v in Counter(locs).items() if v > 1]
    if dup_locs:
        errors.append(f"duplicate sitemap URLs: {dup_locs}")

    sitemap_ids = set()
    for url in locs:
        path = urlparse(url).path
        m = re.search(r"/tortoise-food-db-korea/plant/([^/]+)/?", path)
        if m:
            sitemap_ids.add(m.group(1))
    missing_sitemap = sorted(public_ids - sitemap_ids)
    extra_sitemap = sorted(sitemap_ids - id_set)
    if missing_sitemap:
        errors.append(f"plant ids missing from sitemap: {missing_sitemap}")
    if extra_sitemap:
        errors.append(f"sitemap plant URLs without plants.json id: {extra_sitemap}")

    expected_home = BASE
    if expected_home not in locs:
        errors.append("home URL missing from sitemap")

    bad_canonical = []
    for pid in sorted(id_set & dirs):
        html = (PLANT_DIR / pid / "index.html").read_text(encoding="utf-8")
        expected = f'{BASE}plant/{pid}/'
        m = re.search(r'<link\s+rel="canonical"\s+href="([^"]+)"', html)
        if not m or m.group(1) != expected:
            bad_canonical.append(pid)
    if bad_canonical:
        errors.append(f"missing/wrong canonical on plant pages: {bad_canonical}")

    print(f"plants.json ids: {len(ids)}")\n    print(f"public/indexable ids: {len(public_ids)}")
    print(f"detail pages: {len(dirs)}")
    print(f"sitemap plant URLs: {len(sitemap_ids)}")
    print(f"sitemap total URLs: {len(locs)}")

    if errors:
        for e in errors:
            fail(e)
        return 1
    print("PASS: plant ids, detail pages, sitemap URLs and canonicals are consistent")
    return 0


if __name__ == "__main__":
    sys.exit(main())
