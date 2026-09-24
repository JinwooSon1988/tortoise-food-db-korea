#!/usr/bin/env python3
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
evidence_rows = json.loads((ROOT / "data/public_evidence_records.json").read_text(encoding="utf-8")).get("records", [])
evidence = {row["id"]: row for row in evidence_rows}
assessment_paths = [ROOT / "data/assessments.json"] + sorted((ROOT / "data").glob("assessments_korea_addendum*.json"))

ibera = re.compile(r"(?:Testudo graeca ibera|T\.\s*g\.\s*ibera|이베라)", re.I)
exact_ibera = re.compile(r"Testudo\s+graeca\s+ibera", re.I)
positive_markers = re.compile(r"(?:직접\s*(?:야생)?섭식|직접\s*(?:관찰|근거|자료)|종수준\s*직접)", re.I)
negative_markers = re.compile(r"(?:없|아님|아니|미확립|확립되지|확인되지|확대하지|의미하지|확정하지|직접\s*근거\s*없이|직접\s*위해근거\s*없이)", re.I)
errors = []
checked = 0

for path in assessment_paths:
    if not path.exists():
        continue
    for row in json.loads(path.read_text(encoding="utf-8")):
        checked += 1
        fields = [str(row.get("why", "")), str(row.get("applicability_note", ""))]
        claims = []
        for field in fields:
            for sentence in re.split(r"(?<=[.!?])\s+|\n+", field):
                if ibera.search(sentence) and positive_markers.search(sentence) and not negative_markers.search(sentence):
                    claims.append(sentence)
        if not claims:
            continue
        linked = [evidence[eid] for eid in row.get("evidence_ids", []) if eid in evidence]
        supported = any(
            ev.get("applicability") == "exact_taxon"
            and exact_ibera.search(str(ev.get("animal_taxon", "")))
            for ev in linked
        )
        if not supported:
            errors.append(f"{path.name}:{row.get('plant_id')}: positive Ibera direct-evidence claim lacks exact_taxon T. g. ibera evidence")

if errors:
    raise SystemExit("Ibera claim guard failed:\n- " + "\n- ".join(errors))
print(f"Ibera claim guard passed: {checked} assessments checked.")
