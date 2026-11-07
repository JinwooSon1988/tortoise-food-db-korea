#!/usr/bin/env python3
"""Validate staged primary-literature feeding observations without inferring safety."""
import json
from collections import defaultdict
from pathlib import Path

path = Path("data/primary_literature_observed_feeding_20261104.json")
data = json.loads(path.read_text(encoding="utf-8"))
assert data["source_doi"] == "https://doi.org/10.1371/journal.pone.0116716"
assert data["source_full_text"].startswith("https://pmc.ncbi.nlm.nih.gov/")
assert len(data["records"]) == 10
keys = set()
totals = defaultdict(int)
for r in data["records"]:
    key = (r["verbatim_plant_name"], r["table"], r["period"])
    assert key not in keys, f"duplicate observation: {key}"
    keys.add(key)
    assert r["animal_taxon"] == "Gopherus agassizii"
    assert r["table"] in ("Table 6", "Table 10")
    assert r["period"] == ("early spring" if r["table"] == "Table 6" else "late spring")
    assert isinstance(r["observed_bites"], int) and r["observed_bites"] > 0
    assert r["taxon_id_mapping_status"] == "unverified"
    assert r["feeding_safety_status"] == "unassessed"
    assert r["plant_part"] == "not specified by extracted table"
    totals[r["table"]] += 1
assert totals == {"Table 6": 5, "Table 10": 5}
print("PASS: 10 table-located observations, 0 promoted taxon mappings or safety assessments")
