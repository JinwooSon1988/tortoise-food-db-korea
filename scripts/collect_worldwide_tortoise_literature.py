#!/usr/bin/env python3
"""Worldwide tortoise diet bibliography discovery via OpenAlex.

Discovery only: paper metadata and abstracts are NOT feeding safety evidence.
Every plant-level assertion needs independent full-text or source inspection.
"""
import argparse
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

GENERA = ["Testudo", "Gopherus", "Centrochelys", "Stigmochelys", "Geochelone",
          "Astrochelys", "Pyxis", "Aldabrachelys", "Chelonoidis", "Kinixys",
          "Homopus", "Chersina", "Psammobates", "Indotestudo", "Manouria",
          "Malacochersus", "Agrionemys", "Gopherus", "Chilabothrus"]
# Exclude non-tortoise taxa; keep explicit, reviewed genus inventory.
GENERA = sorted(set(GENERA) - {"Chilabothrus"})
TOPICS = ["diet feeding plants", "food plants foraging", "herbivory vegetation",
          "stomach contents fecal analysis", "nutrition captive husbandry"]
API = "https://api.openalex.org/works"

def get_json(url, retries=3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "GeobukbapEvidenceDiscovery/1.0 (research bibliography)"})
            with urllib.request.urlopen(req, timeout=45) as response:
                return json.load(response)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            if attempt == retries - 1:
                raise
            time.sleep(2 ** attempt)

def reconstruct_abstract(inverted):
    if not isinstance(inverted, dict):
        return None
    words = [(pos, word) for word, positions in inverted.items() for pos in positions]
    return " ".join(w for _, w in sorted(words)) if words else None

def search(query, pages, per_page, email):
    params = {"search": query, "filter": "from_publication_date:1900-01-01",
              "per-page": str(per_page), "page": "1"}
    if email:
        params["mailto"] = email
    for page in range(1, pages + 1):
        params["page"] = str(page)
        data = get_json(API + "?" + urllib.parse.urlencode(params))
        for work in data.get("results", []):
            yield work
        if len(data.get("results", [])) < per_page:
            break

def normalized(work, genus, topic):
    loc = work.get("primary_location") or {}
    source = loc.get("source") or {}
    return {
        "openalex_id": work.get("id"), "doi": work.get("doi"),
        "title": work.get("title"), "year": work.get("publication_year"),
        "publication_date": work.get("publication_date"),
        "source": source.get("display_name"),
        "source_type": work.get("type"),
        "landing_page": loc.get("landing_page_url"),
        "fulltext_url": loc.get("pdf_url"),
        "best_oa_pdf": (work.get("best_oa_location") or {}).get("pdf_url"),
        "pmcid": ((work.get("ids") or {}).get("pmcid") or "").rsplit("/", 1)[-1] or None,
        "language": work.get("language"),
        "is_oa": (work.get("open_access") or {}).get("is_oa"),
        "abstract": reconstruct_abstract(work.get("abstract_inverted_index")),
        "discovery_genus": [genus], "discovery_topic": [topic],
        "review_state": "bibliography_only_not_plant_evidence",
        "plant_taxa": [], "animal_taxon_confirmed": None,
        "plant_part_confirmed": None, "feeding_verdict": None,
        "directness_confirmed": None,
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", type=int, default=2)
    ap.add_argument("--per-page", type=int, default=50)
    ap.add_argument("--genera", default=",".join(GENERA))
    ap.add_argument("--topics", default=";".join(TOPICS))
    ap.add_argument("--out", default="research/generated/worldwide_tortoise_bibliography.json")
    args = ap.parse_args()
    if not 1 <= args.pages <= 20 or not 1 <= args.per_page <= 200:
        ap.error("pages must be 1..20 and per-page 1..200")
    by_id = {}
    failures = []
    for genus in dict.fromkeys(x.strip() for x in args.genera.split(",") if x.strip()):
        for topic in dict.fromkeys(x.strip() for x in args.topics.split(";") if x.strip()):
            query = genus + " " + topic
            try:
                for work in search(query, args.pages, args.per_page, os.environ.get("OPENALEX_EMAIL")):
                    key = work.get("id")
                    if not key:
                        continue
                    if key not in by_id:
                        by_id[key] = normalized(work, genus, topic)
                    else:
                        row = by_id[key]
                        if genus not in row["discovery_genus"]:
                            row["discovery_genus"].append(genus)
                        if topic not in row["discovery_topic"]:
                            row["discovery_topic"].append(topic)
            except Exception as exc:
                failures.append({"genus": genus, "topic": topic, "error": str(exc)})
    rows = sorted(by_id.values(), key=lambda x: (-(x["year"] or 0), x["openalex_id"]))
    result = {"generated_at": datetime.now(timezone.utc).isoformat(),
              "warning": "Search hits are unverified bibliography leads, NOT species feeding evidence.",
              "counts": {"unique_works": len(rows), "failures": len(failures),
                         "by_genus_discovery": dict(Counter(g for r in rows for g in r["discovery_genus"]))},
              "failures": failures, "works": rows}
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["counts"], ensure_ascii=False))
    if failures:
        raise SystemExit("Incomplete worldwide bibliography discovery; inspect failures")

if __name__ == "__main__":
    main()
