#!/usr/bin/env python3
"""Read-only smoke checks for critical existing pages and local JS assets."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
import sys

ROOT = Path(__file__).resolve().parents[1]
PAGES = {
    "index.html": {"lang": "ko", "search": True, "scripts": {"language-toggle.js", "search-live.js"}},
    "en/index.html": {"lang": "en", "search": True, "scripts": {"search-en.js"}},
    "plant/dandelion/index.html": {"lang": "ko", "search": False, "scripts": {"detail-locale-history.js"}},
    "en/plant/dandelion/index.html": {"lang": "en", "search": False, "scripts": {"detail-locale-history.js"}},
    "guides/research-method/index.html": {"lang": "ko", "search": False, "scripts": {"language-toggle.js"}},
    "en/guides/research-method/index.html": {"lang": "en", "search": False, "scripts": set()},
}

class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.lang = ""
        self.ids = set()
        self.scripts = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "html":
            self.lang = a.get("lang", "")
        if a.get("id"):
            self.ids.add(a["id"])
        if tag == "script" and a.get("src"):
            self.scripts.append(a["src"])

errors = []
for name, expected in PAGES.items():
    path = ROOT / name
    if not path.is_file():
        errors.append(f"{name}: missing page")
        continue
    parser = PageParser()
    parser.feed(path.read_text(encoding="utf-8"))
    if parser.lang != expected["lang"]:
        errors.append(f"{name}: expected html lang={expected['lang']}, got {parser.lang!r}")
    if expected["search"] and "searchInput" not in parser.ids:
        errors.append(f"{name}: search input missing")
    script_names = set()
    for src in parser.scripts:
        url = urlsplit(src)
        if url.scheme or url.netloc or src.startswith("//"):
            continue  # External scripts are not repository assets.
        if not url.path or url.path.startswith("/"):
            errors.append(f"{name}: unexpected root-relative script {src}")
            continue
        target = (path.parent / unquote(url.path)).resolve()
        if not target.is_relative_to(ROOT.resolve()):
            errors.append(f"{name}: script escapes repository {src}")
        elif not target.is_file():
            errors.append(f"{name}: missing local script {src}")
        script_names.add(Path(url.path).name)
    for required in expected["scripts"] - script_names:
        errors.append(f"{name}: required script not loaded: {required}")

if errors:
    print("\n".join(errors), file=sys.stderr)
    sys.exit(1)
print(f"PASS: {len(PAGES)} critical pages, local script assets, and language/search structure")
