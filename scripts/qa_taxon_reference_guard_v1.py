#!/usr/bin/env python3
"""Taxon reference guard.

Assessment text (why / applicability_note / limits / note) may name a specific tortoise taxon
(e.g. T. g. ibera, T. hermanni, C. sulcata) or the Mediterranean Testudo group only when the
assessment itself targets that taxon or a linked evidence record actually studied it.
This blocks two failure modes:
  * using a taxon as an implicit reference point for general evidence
    ("not Ibera-direct", "not Mediterranean-Testudo-specific"), and
  * naming a taxon whose evidence is not linked at all.
Positive over-claims are guarded separately by qa_ibera_claim_guard_v1 and
qa_mediterranean_claim_guard_v1.

Known legacy wording is listed in data/taxon_reference_debt_v1.json. The list may only shrink:
new violations fail, and entries that no longer violate must be removed.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
evidence = {r["id"]: r for r in json.loads((ROOT / "data/public_evidence_records.json").read_text(encoding="utf-8")).get("records", [])}
debt_path = ROOT / "data/taxon_reference_debt_v1.json"
debt = json.loads(debt_path.read_text(encoding="utf-8")) if debt_path.exists() else {"entries": []}
paths = [ROOT / "data/public_assessments.json", ROOT / "data/assessments.json"] + sorted((ROOT / "data").glob("assessments_korea_addendum*.json"))

# taxon key -> (pattern in assessment text, pattern that a linked evidence/assessment taxon must match)
TAXA = {
    "Testudo graeca ibera": (r"이베라|T\.\s*g\.\s*ibera|Testudo\s+graeca\s+ibera", r"ibera"),
    "Testudo hermanni": (r"hermanni|헤르만", r"hermanni"),
    "Testudo horsfieldii": (r"horsfieldii|호스필드", r"horsfieldii"),
    "Testudo marginata": (r"marginata|마지나타", r"marginata"),
    "Testudo kleinmanni": (r"kleinmanni|클라인만", r"kleinmanni"),
    "Centrochelys sulcata": (r"sulcata|설카타|Centrochelys", r"sulcata"),
    "Mediterranean Testudo": (r"Mediterranean\s+Testudo|지중해\s*Testudo|지중해\s*육지거북|지중해종", r"Testudo|Mediterranean"),
}
FIELDS = ("why", "applicability_note", "limits", "note")


def texts(row):
    out = []
    for f in FIELDS:
        v = row.get(f)
        if isinstance(v, list):
            out += [str(x) for x in v]
        elif v:
            out.append(str(v))
    return " \n".join(out)


def supported(row, key):
    need = re.compile(TAXA[key][1], re.I)
    if need.search(str(row.get("animal_taxon") or "")):
        return True
    for eid in row.get("evidence_ids", []):
        ev = evidence.get(eid, {})
        if ev.get("applicability") == "composition_only":
            continue
        if key == "Mediterranean Testudo" and ev.get("applicability") == "mediterranean_testudo":
            return True
        if need.search(str(ev.get("animal_taxon") or "")):
            return True
    return False


violations = set()
checked = 0
for path in paths:
    if not path.exists():
        continue
    rows = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(rows, dict):
        rows = rows.get("assessments", rows.get("records", []))
    for row in rows:
        checked += 1
        body = texts(row)
        for key, (pat, _) in TAXA.items():
            if re.search(pat, body, re.I) and not supported(row, key):
                violations.add((path.name, f"{row.get('plant_id')}@{row.get('animal_taxon') or row.get('species_group')}" if path.name == "public_assessments.json" else row.get("plant_id"), key))

listed = {(e["file"], e["plant_id"], e["taxon"]) for e in debt.get("entries", [])}
clean_files = set(debt.get("clean_files", []))
errors = []
for v in sorted(violations - listed):
    errors.append(f"{v[0]}:{v[1]}: names {v[2]} but neither the assessment nor any linked evidence studies that taxon")
for v in sorted(listed - violations):
    errors.append(f"debt entry no longer violates; remove it from taxon_reference_debt_v1.json: {v}")
for v in sorted(listed):
    if v[0] in clean_files:
        errors.append(f"{v[0]} is declared clean and may not carry debt entries: {v}")
if errors:
    sys.exit("Taxon reference guard failed:\n- " + "\n- ".join(errors))
print(f"Taxon reference guard passed: {checked} assessments checked; {len(violations)} legacy debt entries in {len({v[0] for v in violations})} files; clean files: {', '.join(sorted(clean_files))}.")
