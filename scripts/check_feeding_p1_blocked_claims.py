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

# Check that unverified P1 sources are not presented as confirmed feeding
# records in the public pending feed. Compare canonical DOI/URL identifiers.
from urllib.parse import urlsplit

def source_key(value):
    value = value.strip().lower()
    if value.startswith("doi:"):
        return "doi:" + value[4:]
    if value.startswith("https://doi.org/") or value.startswith("http://doi.org/"):
        return "doi:" + value.split("doi.org/", 1)[1]
    if value.startswith("10."):
        return "doi:" + value
    parts = urlsplit(value)
    return parts.netloc + parts.path.rstrip("/") if parts.scheme else value

site = json.loads((ROOT / "data/feeding_pending_site_v1.json").read_text(encoding="utf-8"))
blocked_sources = {source_key(r["source"]) for r in manifest["blocked_claims"]}
# Negative controls: all DOI spellings must match a held source, while
# unrelated DOIs and URLs must not be blocked.
assert source_key("doi:10.1016/j.jaridenv.2005.06.010") in blocked_sources
assert source_key("https://doi.org/10.1016/j.jaridenv.2005.06.010") in blocked_sources
assert source_key("10.1016/j.jaridenv.2005.06.010") in blocked_sources
assert source_key("https://doi.org/10.0000/unrelated") not in blocked_sources
assert source_key("https://example.org/unrelated") not in blocked_sources
for plant_id, feed_records in site["records"].items():
    for feed_record in feed_records:
        assert source_key(feed_record["url"]) not in blocked_sources, (
            f"Unverified P1 source leaked into public feeding records: {plant_id}"
        )
print(f"PASS: no P1 blocked sources in {len(site['records'])} public feeding plant entries")
