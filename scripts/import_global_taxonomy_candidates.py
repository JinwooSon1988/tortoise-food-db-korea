#!/usr/bin/env python3
"""Validate and normalize GBIF candidate JSON without changing feeding verdicts."""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "global_taxonomy_candidates.json"
DEST = ROOT / "data" / "global_taxonomy_candidates.json"
BINOMIAL = re.compile(r"^[A-Z][a-z-]+ [a-z][a-z-]+(?: .*)?$")

def main():
    payload = json.loads(SOURCE.read_text(encoding="utf-8"))
    rows = payload if isinstance(payload, list) else payload.get("records")
    if not isinstance(rows, list):
        raise SystemExit("ERROR: records must be a JSON array")
    normalized, seen, rejected = [], set(), []
    for idx, row in enumerate(rows):
        if not isinstance(row, dict):
            rejected.append((idx, "not an object")); continue
        name = " ".join(str(row.get("scientific_name") or "").split())
        url = str(row.get("source_taxon_url") or "")
        taxon_id = str(row.get("taxon_id") or "")
        if not BINOMIAL.fullmatch(name):
            rejected.append((idx, "not a species-like scientific name")); continue
        if not re.fullmatch(r"https://www\.gbif\.org/species/\d+", url):
            rejected.append((idx, "missing or invalid GBIF source")); continue
        if not re.fullmatch(r"gbif:\d+", taxon_id):
            rejected.append((idx, "invalid taxon_id")); continue
        if name.casefold() in seen:
            rejected.append((idx, "duplicate scientific name")); continue
        seen.add(name.casefold())
        normalized.append({
            "scientific_name": name,
            "family": str(row.get("family") or ""),
            "source_taxon_url": url,
            "taxon_id": taxon_id,
            "identity_status": "taxonomy_candidate",
            "feeding_evidence_status": "not_reviewed",
            "feeding_safety_status": "not_assessed",
        })
    normalized.sort(key=lambda r: r["scientific_name"].casefold())
    out = {"schema_version": "1.0", "record_count": len(normalized), "records": normalized}
    if SOURCE.resolve() == DEST.resolve():
        print("Validating existing canonical file")
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"Accepted: {len(normalized)}; rejected: {len(rejected)}; output: {DEST}")
    if rejected:
        print("First rejected rows:", rejected[:15])
    if not normalized:
        raise SystemExit("ERROR: no valid species candidates")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
