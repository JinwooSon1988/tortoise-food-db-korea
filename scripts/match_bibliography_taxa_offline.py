#!/usr/bin/env python3
"""Offline bibliography-to-taxon candidate matching; NEVER assigns feeding safety."""
import argparse
import json
import re
from collections import Counter
from pathlib import Path

BINOMIAL = re.compile(r"(?<![A-Za-z])([A-Z][a-z]{2,})\s+([a-z][a-z-]{2,})(?![A-Za-z])")
NON_TAXA = {"the", "and", "for", "with", "from", "study", "diet", "food", "plant", "plants", "testudo"}
STOP_PHRASES = {"South Africa", "North America", "South America", "New Zealand", "United States"}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bibliography", default="worker-output/worldwide-literature.json")
    ap.add_argument("--catalog", default="data/plant-catalog")
    ap.add_argument("--output", default="worker-output/bibliography-taxon-candidates.json")
    args = ap.parse_args()
    catalog = {}
    for file in sorted(Path(args.catalog).glob("taxa-??.json")):
        for row in json.loads(file.read_text(encoding="utf-8")).get("records", []):
            scientific = (row.get("scientific") or "").strip()
            parts = scientific.split()
            if len(parts) >= 2 and re.fullmatch(r"[A-Z][a-z-]+", parts[0]) and re.fullmatch(r"[a-z][a-z-]+", parts[1]):
                catalog.setdefault((parts[0] + " " + parts[1]).casefold(), []).append({
                    "taxon_id": row.get("id"), "scientific": scientific
                })
    if not Path(args.bibliography).exists():
        # No downloaded bibliography yet (e.g. a fresh CI checkout or an API cooldown): an empty queue, not an error.
        bibliography = {"works": []}
        print(f"No bibliography at {args.bibliography}; writing an empty candidate list.")
    else:
        bibliography = json.loads(Path(args.bibliography).read_text(encoding="utf-8"))
    works = bibliography.get("works", [])
    output = []
    seen = set()
    counts = Counter()
    for work in works:
        wid = work.get("openalex_id") or work.get("id") or work.get("doi")
        if not wid:
            counts["missing_work_id"] += 1
            continue
        for field in ("title", "abstract"):
            text = work.get(field) or ""
            if not isinstance(text, str):
                continue
            for match in BINOMIAL.finditer(text):
                phrase = match.group(0)
                if phrase in STOP_PHRASES:
                    continue
                key = phrase.casefold()
                if key not in catalog:
                    continue
                for taxon in catalog[key]:
                    unique = (str(wid), str(taxon["taxon_id"]), field)
                    if unique in seen:
                        continue
                    seen.add(unique)
                    excerpt = text[max(0, match.start()-120):min(len(text),match.end()+120)]
                    output.append({
                        "taxon_id": taxon["taxon_id"],
                        "scientific": taxon["scientific"],
                        "matched_name": phrase,
                        "work_id": wid,
                        "doi": work.get("doi"),
                        "title": work.get("title"),
                        "match_field": field,
                        "context_excerpt": excerpt,
                        "status": "bibliography_mention_unverified",
                        "feeding_safety_assessed": False,
                        "review_required": ["confirm taxon identity", "inspect source context and original text",
                                            "confirm tortoise species and feeding event", "verify plant part and provenance"]
                    })
                    counts[field + "_matches"] += 1
    result = {"warning": "A name mention is NOT tortoise consumption or feeding safety evidence.",
              "works_scanned": len(works), "catalog_binomials": len(catalog),
              "unique_taxa_mentioned": len({x["taxon_id"] for x in output}),
              "matches": len(output), "by_field": dict(counts),
              "candidates": output}
    dest = Path(args.output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k,v in result.items() if k != "candidates"}, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
