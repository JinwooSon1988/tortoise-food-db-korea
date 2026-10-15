#!/usr/bin/env python3
"""Record what each The Tortoise Table plant entry used by a public evidence record actually names.

For every plant entry (viewplants/?plant=N) linked from data/public_evidence_records.json this stores the entry's
common name, Latin name, feeding classification and the scientific names written in the entry text (italic names
and "the <Genus> genus"), with the page's SHA-256 and the check date. The page text itself is not stored.

  python scripts/build_tortoise_table_page_taxa_v1.py --live              # fetch each entry (one request per 1.5 s)
  python scripts/build_tortoise_table_page_taxa_v1.py --from-dir DIR      # parse saved pages DIR/p<N>.html

Writes data/tortoise_table_page_taxa_v1.json, read offline by scripts/qa_public_evidence_integrity_v1.py.
"""
import hashlib
import html
import json
import re
import sys
import time
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from evidence_sources import TT_PLANT

OUT = ROOT / "data/tortoise_table_page_taxa_v1.json"
URL = "https://www.thetortoisetable.org.uk/plant-database/viewplants/?plant={}"
UA = "Mozilla/5.0 (tortoise-food-db-korea evidence link check)"
CLASS = re.compile(r"(Safe to Feed|Feed in Moderation|Feed Sparingly|Do not Feed|Do Not Feed)")


def clean(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def parse(raw):
    text = clean(raw)
    h1 = re.findall(r"<h1[^>]*>(.*?)</h1>", raw, re.S)
    latin = re.search(r"Latin Name:\s*(.*?)\s*Family Name", text)
    cls = CLASS.search(text)
    m = re.search(r"Family Name:.*?</ul>\s*</div>(.*?)<div style=\"clear:both;\">", raw, re.S)
    body = m.group(1) if m else ""
    italic = re.findall(r"<(?:i|em)>(.*?)</(?:i|em)>|<span style=\"font-style: ?italic;?\">(.*?)</span>", body, re.S)
    names = [clean(a or b) for a, b in italic]
    names += [g + " (genus)" for g in re.findall(r"\b(?:the|of the) ([A-Z][a-z]+) genus\b", clean(body))]
    names = sorted({n.strip(" ,.;") for n in names if re.match(r"[A-Z][a-z]+", n.strip(" ,.;"))})
    return {"name": clean(h1[0]) if h1 else None, "latin": latin.group(1) if latin else None,
            "classification": cls.group(1).replace("Do Not", "Do not") if cls else None, "taxa_named_in_text": names}


def plant_numbers():
    recs = json.loads((ROOT / "data/public_evidence_records.json").read_text(encoding="utf-8"))["records"]
    return sorted({int(m.group(1)) for r in recs for m in [TT_PLANT.search(str(r.get("url") or ""))] if m})


def main(args):
    pages = {}
    src = Path(args[args.index("--from-dir") + 1]) if "--from-dir" in args else None
    if not src and "--live" not in args:
        sys.exit(__doc__)
    for n in plant_numbers():
        if src:
            raw_b = (src / f"p{n}.html").read_bytes()
        else:
            raw_b = urllib.request.urlopen(urllib.request.Request(URL.format(n), headers={"User-Agent": UA}), timeout=40).read()
            time.sleep(1.5)
        p = parse(raw_b.decode("utf-8", "replace"))
        p.update({"url": URL.format(n), "sha256": hashlib.sha256(raw_b).hexdigest()})
        pages[str(n)] = p
    doc = {"schema_version": "1.0", "checked_at": str(date.today()) if not src else "2026-10-15",
           "method": "Each The Tortoise Table plant entry linked from a public evidence record was fetched (one request per 1.5 s) and parsed: "
                     "heading, Latin name, feeding classification, and scientific names written in the entry text. Page text is not stored.",
           "pages": pages}
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"{len(pages)} entries; {sum(1 for p in pages.values() if not p['latin'])} without a Latin name")


if __name__ == "__main__":
    main(sys.argv[1:])
