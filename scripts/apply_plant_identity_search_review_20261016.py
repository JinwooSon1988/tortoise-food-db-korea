#!/usr/bin/env python3
"""Apply the 2026-10-16 plant identity and search review (애호박 vs 주키니, minari / waterdropwort).

The decision record is data/plant_identity_search_review_20261016.json: each update names the file, the row, the
field, the value before and the value after, with the reason and the sources read. This script writes exactly those
changes. A field is written only while it still holds its "before" value; a field edited later is left as it is and
listed as skipped, so a re-run never undoes a later correction. No row is deleted and no verdict is changed.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEW = json.loads((ROOT / "data/plant_identity_search_review_20261016.json").read_text(encoding="utf-8"))
INDENT = {"data/plants.json": 2, "data/public_assessments.json": 2, "data/korean_search_name_map_v1.json": 2,
          "data/curated_identity_notes.json": 2, "data/i18n/en/catalog_en.json": 1, "data/korean_retail_name_map.json": 2}
NO_FINAL_NEWLINE = {"data/korean_retail_name_map.json"}


def rows_of(doc, rel):
    if rel == "data/i18n/en/catalog_en.json":
        return doc["plants"]
    if rel == "data/korean_search_name_map_v1.json":
        return doc["records"]
    return doc


def main():
    docs, skipped, written = {}, [], 0
    for u in REVIEW["updates"]:
        rel = u["file"]
        doc = docs.setdefault(rel, json.loads((ROOT / rel).read_text(encoding="utf-8")))
        label = f"{rel}:{u['target']}.{u['field']}"
        if rel == "data/curated_identity_notes.json":
            notes, pid = doc["notes"], u["target"]["notes"]
            cur = notes.get(pid)
            if cur == u["after"]:
                continue
            if cur == u["before"]:
                notes[pid] = u["after"]; written += 1
            else:
                skipped.append(label)
            continue
        hits = [r for r in rows_of(doc, rel) if all(r.get(k) == v for k, v in u["target"].items())]
        if u["field"] == "row":  # a whole row added by the review
            if not hits and u["before"] is None:
                rows_of(doc, rel).append(u["after"]); written += 1
            elif hits != [u["after"]]:
                skipped.append(label)
            continue
        assert len(hits) == 1, label
        row, cur = hits[0], hits[0].get(u["field"])
        if cur == u["after"]:
            continue
        if cur == u["before"]:
            row[u["field"]] = u["after"]; written += 1
        else:
            skipped.append(label)
    for rel, doc in docs.items():
        end = "" if rel in NO_FINAL_NEWLINE else "\n"
        (ROOT / rel).write_text(json.dumps(doc, ensure_ascii=False, indent=INDENT[rel]) + end, encoding="utf-8")
    print(f"applied {written} of {len(REVIEW['updates'])} reviewed fields")
    if skipped:
        print("left unchanged (edited after the review):", ", ".join(skipped))


if __name__ == "__main__":
    sys.exit(main())
