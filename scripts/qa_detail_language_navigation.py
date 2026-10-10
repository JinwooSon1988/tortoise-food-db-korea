#!/usr/bin/env python3
"""Require functional language switching and icon-only navigation on every generated plant detail."""
from pathlib import Path
import re
import sys

root = Path(__file__).resolve().parents[1]
errors = []
count = 0
for lang, folder in (("ko", root / "plant"), ("en", root / "en" / "plant")):
    for page in sorted(folder.glob("*/index.html")):
        count += 1
        html = page.read_text(encoding="utf-8")
        nav = re.search(r'<nav class="detailnavlinks"[^>]*>(.*?)</nav>', html, re.S)
        switch = re.search(r'<nav class="langswitch"[^>]*>(.*?)</nav>', html, re.S)
        if not nav or 'class="iconnav-home"' not in nav.group(1) or 'class="iconnav-back"' not in nav.group(1):
            errors.append(f"{page.relative_to(root)}: missing icon navigation")
        if not switch or not re.search(r'<a [^>]*hreflang="ko"', switch.group(1)) or not re.search(r'<a [^>]*hreflang="en"', switch.group(1)):
            errors.append(f"{page.relative_to(root)}: missing clickable KO/EN links")
        if switch and ('?lang=ko' not in switch.group(1) or '?lang=en' not in switch.group(1)):
            errors.append(f"{page.relative_to(root)}: missing explicit language URL")
        if lang == "en" and switch and 'aria-current="page" class="active">English</a>' not in switch.group(1):
            errors.append(f"{page.relative_to(root)}: English choice not active")
if count < 300:
    errors.append(f"Too few generated detail pages: {count}")
if errors:
    print("\n".join(errors[:60]), file=sys.stderr)
    sys.exit(1)
print(f"PASS: {count} Korean and English plant detail pages have accessible icon navigation and functional language links.")
