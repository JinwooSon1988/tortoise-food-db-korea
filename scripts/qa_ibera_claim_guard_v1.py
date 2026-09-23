#!/usr/bin/env python3
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
evidence_rows = json.loads((ROOT / "data/public_evidence_records.json").read_text(encoding="utf-8")).get("records", [])
evidence = {row["id"]: row for row in evidence_rows}
assessment_paths = [ROOT / "data/assessments.json"] + sorted((ROOT / "data").glob("assessments_korea_addendum*.json"))

ibera_claim = re.compile(r"(?:Testudo graeca ibera|T\.\s*g\.\s*ibera|이베라)", re.I)
exact_ibera = re.compile(r"Testudo\s+graeca\s+ibera", re.I)
negative = re.compile(r"(?:없|아님|아니|미확립|확립되지|확인되지|직접자료가 아니|직접[^.]{0,40}(?:아님|아니|없)|확대하지|의미하지|확정하지|확정하지 않|직접 근거 없이|직접 위해근거 없이|직접 근거[^.]{0,40}확립되지|직접[^.]{0,40}확립되지)", re.I)
errors = []
checked = 0

for path in assessment_paths:
    if not path.exists():
        continue
    for row in json.loads(path.read_text(encoding="utf-8")):
        checked += 1
        text = str(row.get("why", "")) + "\n" + str(row.get("applicability_note", ""))
        positive_claim = False
        for match in ibera_claim.finditer(text):
            sentence_start = max(text.rfind(".", 0, match.start()), text.rfind("。", 0, match.start()), text.rfind("\n", 0, match.start()))
            next_dot = text.find(".", match.end())
            sentence_end = len(text) if next_dot < 0 else next_dot + 1
            sentence = text[sentence_start + 1:sentence_end]
            if not negative.search(sentence):
                positive_claim = True
                break
        if not positive_claim:
            continue
        linked = [evidence[eid] for eid in row.get("evidence_ids", []) if eid in evidence]
        supported = any(
            ev.get("applicability") == "exact_taxon"
            and exact_ibera.search(str(ev.get("animal_taxon", "")))
            for ev in linked
        )
        if not supported:
            errors.append(f"{path.name}:{row.get('plant_id')}: positive Ibera-specific claim lacks exact_taxon T. g. ibera evidence")

if errors:
    raise SystemExit("Ibera claim guard failed:\n- " + "\n- ".join(errors))
print(f"Ibera claim guard passed: {checked} assessments checked.")
