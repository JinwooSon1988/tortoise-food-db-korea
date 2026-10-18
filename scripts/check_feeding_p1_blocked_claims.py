#!/usr/bin/env python3
"""Fail closed if the P1 blocked-claim manifest drifts from verification records."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
records = json.loads((ROOT / "data/feeding_record_verification_v1.json").read_text(encoding="utf-8"))["records"]
manifest = json.loads((ROOT / "data/feeding_p1_blocked_claim_manifest_20261018.json").read_text(encoding="utf-8"))
blocked = [r for r in records if r["verification_status"] == "original_inaccessible"]
assert manifest["blocked_claim_count"] == len(manifest["blocked_claims"]), "Manifest count mismatch"
assert len(blocked) == len(manifest["blocked_claims"]), "Missing or extra blocked records"
def identity(r):
    return (
        tuple(r["evidence_ids"]),
        r.get("plant_id"),
        r["plant_taxon_reported"] if "plant_taxon_reported" in r else r["reported_taxon"],
        r["tortoise_taxon"],
        r["source"],
    )
assert sorted(map(repr, map(identity, blocked))) == sorted(map(repr, map(identity, manifest["blocked_claims"]))), "Blocked claim identity drift"
assert all(r["status"] == "hold" for r in manifest["blocked_claims"]), "Non-hold blocked claim"
print(f"PASS: {len(blocked)} original-inaccessible records held; no missing or mismatched claims")
