#!/usr/bin/env python3
"""Guard existing Korean/English navigation against stale or looping links."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse, parse_qs
import sys

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://jinwooson1988.github.io/tortoise-food-db-korea/"
PAIRS = [
    ("plant/dandelion/index.html", "en/plant/dandelion/index.html"),
    ("guides/research-method/index.html", "en/guides/research-method/index.html"),
]

class SwitchParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.depth = 0
        self.links = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "nav" and "langswitch" in a.get("class", "").split():
            self.depth += 1
        elif self.depth and tag == "nav":
            self.depth += 1
        elif self.depth and tag == "a" and a.get("hreflang") in ("ko", "en"):
            self.links.append((a["hreflang"], a.get("href", "")))
    def handle_endtag(self, tag):
        if tag == "nav" and self.depth:
            self.depth -= 1

errors = []
for ko, en in PAIRS:
    for current, counterpart, lang in ((ko, en, "en"), (en, ko, "ko")):
        html = (ROOT / current).read_text(encoding="utf-8")
        parser = SwitchParser()
        parser.feed(html)
        links = [href for target, href in parser.links if target == lang]
        if len(links) != 1:
            errors.append(f"{current}: expected exactly one {lang} switch, found {len(links)}")
            continue
        current_url = urljoin(BASE, current.replace("index.html", ""))
        target = urlparse(urljoin(current_url, links[0]))
        expected = urlparse(urljoin(BASE, counterpart.replace("index.html", "")))
        if target.path.rstrip("/") != expected.path.rstrip("/"):
            errors.append(f"{current}: switch points to wrong page {target.path}")
        if parse_qs(target.query).get("lang") != [lang]:
            errors.append(f"{current}: switch must set ?lang={lang} to override stored preference")
if errors:
    print("\n".join(errors), file=sys.stderr)
    sys.exit(1)
print(f"PASS: {len(PAIRS)} bilingual navigation pairs and explicit locale preferences")
