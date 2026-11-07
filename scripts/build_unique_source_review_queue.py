#!/usr/bin/env python3
"""Build/check the source-first, UNVERIFIED literature review queue.

Read the authoritative taxon->lead index directly; never promote title matches
to feeding evidence.  --check is read-only and fails if committed output drifts.
"""
import argparse
import json
import pathlib
import re
import sys
from collections import Counter
from urllib.parse import urlsplit, urlunsplit

TORTOISE = re.compile(r"\b(?:tortoises?|testudinidae|testudo|geochelone|centrochelys|chelonoidis|stigmochelys|astrochelys|aldabrachelys|gopherus|kinixys|homopus|psammobates|manouria|indotestudo|malacochersus|agrionemys|pyxis|chersina)\b", re.I)
FEEDING = re.compile(r"\b(?:diet|dietary|feed(?:ing|s)?|forag(?:e|ing)|graz(?:e|ing)|herbivor(?:e|y)|food|nutrition|consum(?:e|ption)|ingest(?:ion|ed)|browse|gut contents?|stomach contents?)\b", re.I)

def canonical_url(url):
    if not isinstance(url, str):
        raise ValueError("Source URL must be a string")
    p = urlsplit(url)
    if p.scheme.lower() != "https" or not p.hostname or p.username or p.password:
        raise ValueError("Invalid HTTPS source URL: " + url)
    host = p.hostname.lower()
    path = p.path.rstrip("/")
    if host in ("doi.org", "dx.doi.org"):
        host = "doi.org"
        path = "/" + path.lstrip("/").lower()
    return urlunsplit(("https", host + ((":" + str(p.port)) if p.port else ""), path, p.query, ""))

def build(index):
    data = json.loads(pathlib.Path(index).read_text(encoding="utf-8"))
    taxa = data.get("taxa")
    if not isinstance(taxa, dict):
        raise ValueError("Missing taxa mapping")
    sources = {}
    for taxon, groups in sorted(taxa.items()):
        if not re.fullmatch(r"gbif:\d+", taxon):
            raise ValueError("Invalid taxon ID: " + taxon)
        for lead in groups.get("literature_leads", []):
            if lead.get("verification") != "search_hit_unreviewed" or lead.get("feeding_safety_status") != "unassessed":
                raise ValueError("Unreviewed literature was promoted to verified evidence")
            url = canonical_url(lead.get("url"))
            title = re.sub(r"<[^>]+>", " ", lead.get("title") or "").strip()
            signals = int(bool(TORTOISE.search(title))) + int(bool(FEEDING.search(title)))
            item = sources.setdefault(url, {"source_url": url, "title": title, "priority": 2, "review_status": "not_reviewed", "feeding_safety_status": "unassessed", "taxon_associations": []})
            item["priority"] = min(item["priority"], 2 - signals)
            if not item["title"] and title:
                item["title"] = title
            if any(a["taxon_id"] == taxon for a in item["taxon_associations"]):
                raise ValueError("Duplicate source-taxon link: " + taxon + " " + url)
            item["taxon_associations"].append({"taxon_id": taxon, "association_verified": False})
    records = sorted(sources.values(), key=lambda r: (r["priority"], -len(r["taxon_associations"]), r["source_url"]))
    counts = Counter(r["priority"] for r in records)
    return {"schema_version": "1.0", "warning": "Title-based review queue only; no feeding or safety claims verified.",
            "counts": {"unique_sources": len(records), "source_taxon_links": sum(len(r["taxon_associations"]) for r in records),
                       "priority_0": counts[0], "priority_1": counts[1], "priority_2": counts[2]},
            "records": records}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", default="data/research_source_leads_index.json")
    p.add_argument("--output", default="data/research_unique_source_review_queue.json")
    p.add_argument("--check", action="store_true", help="Read-only check of committed counts and source associations")
    args = p.parse_args()
    expected = build(args.input)
    dest = pathlib.Path(args.output)
    if args.check:
        actual = json.loads(dest.read_text(encoding="utf-8"))
        if actual["counts"] != expected["counts"]:
            raise SystemExit("FAIL: committed queue counts differ from source index")
        for name, data in (("committed", actual), ("rebuilt", expected)):
            links = {(r["source_url"], a["taxon_id"]) for r in data["records"] for a in r["taxon_associations"]}
            if len(links) != data["counts"]["source_taxon_links"]:
                raise SystemExit("FAIL: duplicate source-taxon association in " + name)
            if name == "committed":
                saved = links
            elif links != saved:
                raise SystemExit("FAIL: source-taxon associations drifted")
        print(json.dumps({"status": "pass", **expected["counts"]}))
    else:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(expected, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
        print(json.dumps(expected["counts"]))

if __name__ == "__main__":
    main()
