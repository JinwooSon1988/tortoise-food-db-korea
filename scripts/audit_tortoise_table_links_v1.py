#!/usr/bin/env python3
"""The Tortoise Table evidence links must open the page of the plant the evidence record describes.

data/tortoise_table_link_audit_20261010.json holds, for every evidence record linking to thetortoisetable.org.uk,
the URL and what that page showed when checked (common name, Latin name, feeding classification).

  python scripts/audit_tortoise_table_links_v1.py          # CI, no network: records use the audited URLs, and a
                                                           # classification stated in `supports` equals the audited one
  python scripts/audit_tortoise_table_links_v1.py --live   # re-fetch every audited page (1.5 s apart) and compare

The site's plant IDs are not stable identifiers on their own; on 2026-10-10 nineteen records pointed at other plants
(e.g. Sorrel -> Michaelmas Daisy, Tagetes -> Oleander). Corrections are listed in the audit file.
"""
import html, json, re, sys, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "data/tortoise_table_link_audit_20261010.json"
EVID = ROOT / "data/public_evidence_records.json"
CLASSES = ("Safe to Feed", "Feed in Moderation", "Feed Sparingly", "Do not Feed")


def stated_classes(text):
    """Classification labels as written by the source (title case); lower-case advice such as
    "succulent, feed in moderation" is not a classification."""
    t = str(text or "")
    return {c for c in CLASSES if c in t}


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (tortoise-food-db-korea evidence link check)"})
    raw = urllib.request.urlopen(req, timeout=40).read().decode("utf-8", "replace")
    text = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", raw)))
    h1 = re.findall(r"<h1[^>]*>(.*?)</h1>", raw, re.S)
    latin = re.search(r"Latin Name:\s*(.*?)\s*Family Name", text)
    cls = re.search(r"(Safe to Feed|Feed in Moderation|Feed Sparingly|Do not Feed|Do Not Feed)", text)
    return {"name": html.unescape(re.sub(r"<[^>]+>", "", h1[0])).strip() if h1 else None,
            "latin": latin.group(1) if latin else None,
            "classification": cls.group(1).replace("Do Not", "Do not") if cls else None}


def main(live):
    audit = {r["record_id"]: r for r in json.loads(AUDIT.read_text(encoding="utf-8"))["records"]}
    records = [r for r in json.loads(EVID.read_text(encoding="utf-8"))["records"] if "thetortoisetable" in str(r.get("url"))]
    errors = []
    for r in records:
        a = audit.get(r["id"])
        if a is None:
            errors.append(f"{r['id']}: Tortoise Table link not covered by the link audit"); continue
        if r["url"] != a["url"]:
            errors.append(f"{r['id']}: url {r['url']} differs from audited {a['url']}")
        if a.get("classification") and stated_classes(r.get("supports")) - {a["classification"]}:
            errors.append(f"{r['id']}: supports states {sorted(stated_classes(r.get('supports')))} but the page says {a['classification']}")
    if live:
        for rid, a in audit.items():
            if "plant=" not in a["url"]:
                continue
            now = fetch(a["url"]); time.sleep(1.5)
            for k in ("name", "latin", "classification"):
                if a.get(k) and now.get(k) != a[k]:
                    errors.append(f"{rid}: live {k} {now.get(k)!r} != audited {a[k]!r} ({a['url']})")
    if errors:
        for e in errors: print("ERROR:", e)
        sys.exit(f"Tortoise Table link audit FAILED: {len(errors)} error(s)")
    print(f"OK: {len(records)} Tortoise Table evidence links use audited URLs{' and match the live pages' if live else ''}")


if __name__ == "__main__":
    main("--live" in sys.argv)
