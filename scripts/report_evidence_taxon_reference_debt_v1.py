#!/usr/bin/env python3
"""Diagnostic report for legacy Ibera-specific wording inside evidence records.

This is intentionally diagnostic-only: it does not rewrite data, alter verdicts,
or fail CI. It identifies reader-facing evidence records that mention
T. graeca ibera / Ibera while their evidence record itself targets a broader
or different animal scope. Exact-taxon Ibera records are retained as legitimate
species-specific evidence.

Use this report while shrinking the legacy wording debt without silently
generalizing genuine species-specific evidence.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
rows = json.loads((ROOT / "data/public_evidence_records.json").read_text(encoding="utf-8")).get("records", [])

IBERA = re.compile(r"(?:Testudo\s+graeca\s+ibera|T\.\s*g\.\s*ibera|Ibera|이베라)", re.I)
EXACT = re.compile(r"Testudo\s+graeca\s+ibera", re.I)
FIELDS = ("source_title", "supports", "does_not_support", "limitations", "scope_note", "animal_taxon")

hits = []
for row in rows:
    taxon = str(row.get("animal_taxon") or "")
    if EXACT.search(taxon):
        continue
    for field in FIELDS:
        value = row.get(field)
        if isinstance(value, list):
            values = [str(v) for v in value]
        elif value:
            values = [str(value)]
        else:
            values = []
        for value in values:
            if IBERA.search(value):
                hits.append({
                    "id": row.get("id"),
                    "field": field,
                    "animal_taxon": taxon,
                    "applicability": row.get("applicability"),
                    "source_type": row.get("source_type"),
                    "text": value,
                })

print(f"Legacy non-Ibera evidence wording candidates: {len(hits)}")
for item in hits:
    print(json.dumps(item, ensure_ascii=False))
