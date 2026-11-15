#!/usr/bin/env python3
"""Fetch GBIF plant taxonomic identity candidates, NOT tortoise feeding evidence.

Writes review-only JSONL compatible with stage_plant_bulk_stream.py.
Requires network; uses documented GBIF species/search paging.
"""
import argparse
import json
import os
import tempfile
import time
from datetime import date
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API = "https://api.gbif.org/v1/species/search"


def fetch_page(offset, limit, opener=urlopen):
    url = API + "?" + urlencode({"rank": "SPECIES", "highertaxon_key": 6,
                                  "limit": limit, "offset": offset})
    request = Request(url, headers={"User-Agent": "GeobukbapResearch/1.0 (https://github.com/JinwooSon1988/tortoise-food-db-korea)",
                                    "Accept": "application/json"})
    for attempt in range(4):
        try:
            with opener(request, timeout=45) as response:
                return json.load(response)
        except (HTTPError, URLError, TimeoutError):
            if attempt == 3:
                raise
            time.sleep(min(2 ** attempt, 8))


def collect(output, pages=25, page_size=1000, fetcher=fetch_page):
    if not 1 <= pages <= 100 or not 1 <= page_size <= 1000:
        raise ValueError("pages must be 1..100 and page_size 1..1000")
    if output.exists():
        raise FileExistsError("use a new output path; never overwrite collected candidates")
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, tempname = tempfile.mkstemp(prefix=".gbif-", suffix=".jsonl", dir=output.parent)
    count = 0
    seen = set()
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            for page in range(pages):
                payload = fetcher(page * page_size, page_size)
                if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
                    raise ValueError("unexpected GBIF API response")
                for taxon in payload["results"]:
                    if (taxon.get("kingdom") != "Plantae"
                            or taxon.get("rank") != "SPECIES"
                            or taxon.get("taxonomicStatus") != "ACCEPTED"):
                        continue
                    key, name = taxon.get("key"), taxon.get("canonicalName")
                    if not isinstance(key, int) or not isinstance(name, str) or not name.strip():
                        continue
                    if key in seen:
                        continue
                    seen.add(key)
                    row = {"scientific_name": name, "source_id": "GBIF",
                           "source_record_id": str(key),
                           "source_url": f"https://www.gbif.org/species/{key}",
                           "family": taxon.get("family") or None,
                           "taxonomic_status": "accepted",
                           "observed_at": date.today().isoformat()}
                    stream.write(json.dumps(row, ensure_ascii=False) + "\n")
                    count += 1
                if payload.get("endOfRecords") is True:
                    break
        if count == 0:
            raise ValueError("zero eligible plant records; refusing to publish empty candidate feed")
        os.replace(tempname, output)
    finally:
        if os.path.exists(tempname):
            os.unlink(tempname)
    return {"candidates": count, "output": str(output), "feed_review_status": "identity_only"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--pages", type=int, default=25)
    parser.add_argument("--page-size", type=int, default=1000)
    args = parser.parse_args()
    print(json.dumps(collect(args.output, args.pages, args.page_size), ensure_ascii=False))


if __name__ == "__main__":
    main()
