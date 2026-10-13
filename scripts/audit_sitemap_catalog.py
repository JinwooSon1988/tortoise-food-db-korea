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
# Validate multilingual alternates on all sitemap entries, not only the catalog.
XHTML = "{http://www.w3.org/1999/xhtml}link"
SM = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
entries = tree.findall(f".//{SM}url")
listed = set(urls)
entries_by_loc = {entry.findtext(f"{SM}loc"): entry for entry in entries}
assert len(entries_by_loc) == len(entries), "Duplicate sitemap loc entries"
for entry in entries:
    loc = entry.findtext(f"{SM}loc")
    alternates = {}
    for link in entry.findall(XHTML):
        lang, href = link.get("hreflang"), link.get("href")
        assert lang and href, f"Malformed hreflang on {loc}"
        assert lang not in alternates, f"Duplicate {lang} hreflang on {loc}"
        assert href in listed, f"Alternate not indexed in sitemap: {loc} -> {href}"
        alternates[lang] = href
    if alternates:
        assert alternates.get("ko") and alternates.get("en"), f"Incomplete language pair: {loc}"
        assert alternates.get("x-default") in (alternates["ko"], alternates["en"]), f"Invalid x-default: {loc}"
        for href in (alternates["ko"], alternates["en"]):
            peer = entries_by_loc[href]
            peer_alternates = {link.get("hreflang"): link.get("href") for link in peer.findall(XHTML)}
            assert peer_alternates == alternates, f"Nonreciprocal hreflang: {loc} <-> {href}"
# Each indexed sitemap URL must resolve to an existing, indexable, self-canonical HTML page.
from html.parser import HTMLParser
from urllib.parse import unquote

class SEOHeadParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.canonicals = []
        self.robots = []
        self.alternates = {}
        self.html_languages = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "html":
            self.html_languages.append(attrs.get("lang", "").lower())
        if tag == "link" and attrs.get("rel", "").lower() == "canonical":
            self.canonicals.append(attrs.get("href", ""))
        if tag == "link" and attrs.get("rel", "").lower() == "alternate" and attrs.get("hreflang"):
            lang = attrs["hreflang"]
            assert lang not in self.alternates, f"Duplicate HTML hreflang: {lang}"
            self.alternates[lang] = attrs.get("href", "")
        if tag == "meta" and attrs.get("name", "").lower() == "robots":
            self.robots.append(attrs.get("content", "").lower())

sitemap_alternates = {
    entry.findtext(f"{SM}loc"): {link.get("hreflang"): link.get("href") for link in entry.findall(XHTML)}
    for entry in entries
}
for url in urls:
    relative = unquote(url[len(BASE):])
    assert relative == "" or (relative.endswith("/") and ".." not in relative.split("/")), f"Unsafe sitemap path: {url}"
    target = ROOT / relative / "index.html"
    assert target.is_file(), f"Sitemap URL has no local HTML page: {url}"
    parser = SEOHeadParser()
    parser.feed(target.read_text(encoding="utf-8"))
    expected_language = "en" if relative.startswith("en/") else "ko"
    assert parser.html_languages == [expected_language], f"HTML lang mismatch: {url} -> {parser.html_languages}"
    assert parser.canonicals == [url], f"Canonical mismatch: {url} -> {parser.canonicals}"
    assert parser.alternates == sitemap_alternates[url], f"HTML/sitemap hreflang mismatch: {url} -> HTML {parser.alternates} vs XML {sitemap_alternates[url]}"
    assert not any("noindex" in value for value in parser.robots), f"Noindex page in sitemap: {url}"

page = (ROOT / "all-plants/index.html").read_text(encoding="utf-8")
assert '<meta name="robots" content="index,follow">' in page, "Catalog is not indexable"
assert f'<link rel="canonical" href="{BASE}all-plants/">' in page, "Catalog canonical mismatch"
redirect = (ROOT / "en/all-plants/index.html").read_text(encoding="utf-8")
assert 'content="noindex,follow"' in redirect, "English redirect indexability changed; revisit sitemap policy"
assert 'hreflang="en"' not in page, "Indexable catalog advertises English noindex redirect"
print(f"PASS: {len(urls)} sitemap URLs, canonical catalog and redirect policy")
