from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "data/species_evidence_primary_source_audit_v56.json"

audit = json.loads(AUDIT.read_text(encoding="utf-8"))
assert audit.get("schema_version") == "5.6"
rows = audit.get("records", [])
assert rows, "primary-source audit records required"

allowed = {"verified_primary", "hold_unverified", "hold_source_conflict"}
seen = set()

def evidence_ids(payload):
    records = payload.get("records")
    if records is None:
        records = payload.get("evidence_records")
    if records is None:
        records = payload.get("evidence")
    assert isinstance(records, list) and records
    return {r.get("id") or r.get("source_id") for r in records}

for row in rows:
    asset = row.get("asset")
    record_id = row.get("record_id")
    status = row.get("status")
    assert asset and record_id, "asset and record_id required"
    key = (asset, record_id)
    assert key not in seen, f"duplicate audit row: {key}"
    seen.add(key)
    assert status in allowed, f"{record_id}: unsupported audit status {status}"
    assert isinstance(row.get("verification"), str) and row["verification"].strip()
    assert isinstance(row.get("scope"), str) and row["scope"].strip()

    path = ROOT / asset
    assert path.is_file(), f"{record_id}: evidence asset missing: {asset}"
    payload = json.loads(path.read_text(encoding="utf-8"))
    ids = evidence_ids(payload)
    assert record_id in ids, f"{record_id}: audit row does not resolve to a stored evidence record"

verified = sum(r["status"] == "verified_primary" for r in rows)
held = len(rows) - verified
assert held > 0, "audit gate must preserve unresolved/conflicting records rather than silently treating all as verified"
print(f"Primary-source audit PASS: {len(rows)} records; {verified} verified, {held} held")
