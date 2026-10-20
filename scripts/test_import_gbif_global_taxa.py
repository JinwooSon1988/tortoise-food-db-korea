#!/usr/bin/env python3
"""Offline regression checks for GBIF global intake normalization."""
import importlib.util
from pathlib import Path
root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("gbif_intake", root / "scripts/import_gbif_global_taxa.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
sample = {"key": 12345, "canonicalName": "Plantago major",
          "kingdom": "Plantae", "rank": "SPECIES",
          "taxonomicStatus": "ACCEPTED", "family": "Plantaginaceae"}
r = mod.normalize(sample)
assert r["candidate_id"] == "gbif_12345"
assert r["feeding_verdict"] is None
assert r["source"]["supports_feeding_claim"] is False
assert r["feeding_evidence_status"] == "not_searched"
for mutation in ({"kingdom": "Animalia"}, {"rank": "GENUS"},
                 {"taxonomicStatus": "SYNONYM"}, {"family": None},
                 {"canonicalName": "Plantago"}):
    assert mod.normalize({**sample, **mutation}) is None, mutation
print("GBIF intake normalization: PASS")
